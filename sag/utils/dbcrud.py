"""
Utility: DBCRUD

A reusable CRUD helper for Django function-based views.

Purpose
-------
This utility reduces boilerplate code in views by centralizing common
CRUD patterns such as:
- listing objects
- retrieving a single object
- creating records
- updating records
- deleting records

It supports:
1) Simple CRUD:
   - One Model
   - One ModelForm

2) Complex CRUD (Parent + Children):
   - One parent ModelForm
   - One inline FormSet (child rows)
   - Correct save order (parent first, then children)

Design Principles
-----------------
- Views control redirects and messages
- DBCRUD only handles database logic
- All write operations are transaction-safe
- Errors are returned, not swallowed
"""

from typing import Type, Optional, Dict, Any
from django import forms
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError, Model
from django.shortcuts import get_object_or_404


class DBCRUD:
    """
    Generic CRUD handler for Django views.

    Parameters
    ----------
    model : Django Model class
        The database model to operate on

    form_class : ModelForm (optional)
        Used for create and update operations

    formset_class : InlineFormSet (optional)
        Used when handling parent + child objects

    set_created_by : bool
        If True, automatically assigns request.user to `created_by`
    """

    def __init__(
        self,
        model: Type[Model],
        form_class: Optional[Type[forms.ModelForm]] = None,
        formset_class: Optional[Any] = None,
        set_created_by: bool = False,
    ):
        self.model = model
        self.form_class = form_class
        self.formset_class = formset_class
        self.set_created_by = set_created_by

    # LIST
    
    def list(self, filters: Optional[Dict[str, Any]] = None):
        """
        Return queryset for listing objects.

        If filters are provided, they are passed to `.filter()`.
        """
        if filters:
            return self.model.objects.filter(**filters)
        return self.model.objects.all()

    # GET
    
    def get(self, pk):
        """
        Fetch a single object by primary key or raise 404.
        """
        return get_object_or_404(self.model, pk=pk)

    # CREATE (Simple: one form, one model)
    
    @transaction.atomic
    def handle_create(self, request, form_kwargs: Optional[Dict[str, Any]] = None):
        """
        Handle creation of a single model instance.

        GET  -> returns empty form
        POST -> validates and saves form

        Returns a dict describing the result.
        """
        if self.form_class is None:
            raise RuntimeError("form_class is required for create")

        # GET request → show empty form
        if request.method != "POST":
            return {
                "action": "render",
                "form": self.form_class(),
                "success": None,
                "errors": None,
            }

        try:
            form = self.form_class(request.POST, **(form_kwargs or {}))

            if form.is_valid():
                obj = form.save(commit=False)

                # Optional created_by handling
                if self.set_created_by and hasattr(obj, "created_by"):
                    obj.created_by = request.user

                obj.save()

                return {
                    "action": "redirect",
                    "object": obj,
                    "success": True,
                    "errors": None,
                }

            return {
                "action": "render",
                "form": form,
                "success": False,
                "errors": form.errors,
            }

        except (IntegrityError, ValidationError) as e:
            return {
                "action": "render",
                "form": self.form_class(request.POST),
                "success": False,
                "errors": str(e),
            }

    # UPDATE (Simple: can update only one form)
    
    @transaction.atomic
    def handle_update(self, request, pk, form_kwargs: Optional[Dict[str, Any]] = None):
        """
        Update an existing object.

        GET  -> pre-filled form
        POST -> validate and save changes
        """
        if self.form_class is None:
            raise RuntimeError("form_class is required for update")

        instance = self.get(pk)

        if request.method != "POST":
            return {
                "action": "render",
                "form": self.form_class(instance=instance),
                "success": None,
                "errors": None,
            }

        try:
            form = self.form_class(
                request.POST,
                instance=instance,
                **(form_kwargs or {}),
            )

            if form.is_valid():
                obj = form.save()
                return {
                    "action": "redirect",
                    "object": obj,
                    "success": True,
                    "errors": None,
                }

            return {
                "action": "render",
                "form": form,
                "success": False,
                "errors": form.errors,
            }

        except (IntegrityError, ValidationError) as e:
            return {
                "action": "render",
                "form": self.form_class(instance=instance),
                "success": False,
                "errors": str(e),
            }

    # CREATE (Parent + FormSet : create/save two forms parent and its child)
    @transaction.atomic
    def handle_create_with_formset(self, request):
        """
        Handle creation of a parent object with related child objects.

        Example:
        - SalesOrder + SalesOrderItemFormSet
        - Quotation + QuotationItemFormSet
        """
        if not self.form_class or not self.formset_class:
            raise RuntimeError("form_class and formset_class are required")

        # GET → empty parent form + empty formset
        if request.method != "POST":
            return {
                "action": "render",
                "form": self.form_class(),
                "formset": self.formset_class(),
                "success": None,
                "errors": None,
            }

        try:
            form = self.form_class(request.POST)
            formset = self.formset_class(request.POST)

            if form.is_valid() and formset.is_valid():
                parent = form.save(commit=False)

                if self.set_created_by and hasattr(parent, "created_by"):
                    parent.created_by = request.user

                parent.save()

                # Attach children to parent
                formset.instance = parent
                formset.save()

                return {
                    "action": "redirect",
                    "object": parent,
                    "success": True,
                    "errors": None,
                }

            return {
                "action": "render",
                "form": form,
                "formset": formset,
                "success": False,
                "errors": form.errors or formset.errors,
            }

        except (IntegrityError, ValidationError) as e:
            return {
                "action": "render",
                "form": self.form_class(request.POST),
                "formset": self.formset_class(request.POST),
                "success": False,
                "errors": str(e),
            }

    # UPDATE (Parent + FormSet)
    @transaction.atomic
    def handle_update_with_formset(self, request, pk):
        """
        Update a parent object and its related children.
        """
        if not self.form_class or not self.formset_class:
            raise RuntimeError("form_class and formset_class are required")

        instance = self.get(pk)

        if request.method != "POST":
            return {
                "action": "render",
                "form": self.form_class(instance=instance),
                "formset": self.formset_class(instance=instance),
                "success": None,
                "errors": None,
            }

        form = self.form_class(request.POST, instance=instance)
        formset = self.formset_class(request.POST, instance=instance)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            return {
                "action": "redirect",
                "object": instance,
                "success": True,
                "errors": None,
            }

        return {
            "action": "render",
            "form": form,
            "formset": formset,
            "success": False,
            "errors": form.errors or formset.errors,
        }

    # DELETE
    @transaction.atomic
    def handle_delete(self, request, pk):
        """
        Delete an object safely.

        GET  -> confirmation screen
        POST -> attempt deletion
        """
        instance = self.get(pk)

        if request.method != "POST":
            return {
                "action": "render",
                "object": instance,
                "success": None,
                "errors": None,
            }

        try:
            instance.delete()
            return {
                "action": "redirect",
                "success": True,
                "errors": None,
            }

        except ProtectedError:
            return {
                "action": "render",
                "object": instance,
                "success": False,
                "errors": "Cannot delete: record is linked to other data",
            }
