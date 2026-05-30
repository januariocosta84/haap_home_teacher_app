# Epic 3: Equipment Registration and Support Requests - Implementation Guide

## Overview

This document provides a comprehensive overview of the implementation of Epic 3 for the HAAP application. This epic covers equipment registration and tracking, assignment management, and teacher support requests.

---

## 1. Equipment Registration (MoE-16)

### Models

#### Equipment Model (`equipment/models.py`)
- **Fields:**
  - `id` (UUID): Primary key
  - `equipment_type`: Type of equipment (tablet, projector, screen, adapter)
  - `model_number`: Equipment model
  - `serial_number`: Unique serial number
  - `preschool`: Foreign key to Preschool
  - `classroom`: Foreign key to Classroom
  - `teacher`: Foreign key to User (teacher)
  - `status`: Active, Inactive, Damaged, Retired
  - `notes`: Additional notes
  - `created_at`: Timestamp
  - `updated_at`: Timestamp

#### EquipmentAssignmentHistory Model
- Tracks all equipment assignment changes
- Stores old and new values for preschool, classroom, and teacher
- Records who made the change and when
- Stores change reason

### Views

#### EquipmentCreateView
- Admin only access
- Creates new equipment records
- Validates model number and serial number uniqueness

#### EquipmentListView
- Lists all equipment with filtering options
- Filter by:
  - Equipment type
  - Status
  - Preschool
  - Serial number / model (search)
- Pagination: 20 items per page

#### EquipmentDetailView
- Shows equipment details
- Displays assignment history

#### EquipmentUpdateView
- Allows editing equipment information
- Automatically logs assignment changes

#### EquipmentByPreschoolView
- Lists equipment assigned to a specific preschool

#### EquipmentByClassroomView
- Lists equipment assigned to a specific classroom

#### EquipmentByTeacherView
- Lists equipment assigned to a specific teacher

### Forms

#### EquipmentForm (`equipment/forms.py`)
- Fields: equipment_type, model_number, serial_number, preschool, classroom, teacher, status, notes
- Dynamic classroom loading based on selected preschool
- Validation to ensure classroom belongs to selected preschool

### URLs

```
/equipment/add/ - Create new equipment
/equipment/list/ - List all equipment
/equipment/<uuid:pk>/ - View equipment details
/equipment/<uuid:pk>/edit/ - Edit equipment
/equipment/<uuid:pk>/assignment/ - Change assignment
/equipment/<uuid:pk>/delete/ - Delete equipment
/equipment/preschool/<uuid:preschool_id>/ - List by preschool
/equipment/classroom/<uuid:classroom_id>/ - List by classroom
/equipment/teacher/<uuid:teacher_id>/ - List by teacher
/equipment/ajax/load-classrooms/ - AJAX endpoint for classroom loading
```

### Templates

- `templates/equipment/equipment_form.html` - Create/Edit form
- `templates/equipment/equipment_list.html` - List view with filters
- `templates/equipment/equipment_detail.html` - Detail view with history
- `templates/equipment/equipment_assignment_form.html` - Assignment change form

---

## 2. Equipment Assignment Changes (MoE-17)

### Views

#### EquipmentAssignmentChangeView
- Allows admin to:
  - **Reassign**: Move equipment to new location/teacher
  - **Delete**: Remove equipment assignment
  - **Retire**: Mark equipment as retired
- Automatically creates EquipmentAssignmentHistory record
- Logs timestamp and previous assignment

### Features
- Change history is retained
- Each change records:
  - Old assignment (preschool, classroom, teacher)
  - New assignment
  - Who made the change
  - When it was changed
  - Reason for change

### Assignment History Viewing
- Available in equipment detail page
- Shows chronological list of all changes
- Displays old/new values for each change

---

## 3. Teacher Support Requests (MoE-18)

### Models

#### SupportTicket Model
- **Fields:**
  - `id` (UUID): Primary key
  - `ticket_number`: Unique auto-generated ticket number (format: TKT-XXXXXX)
  - `teacher`: Foreign key to User (teacher)
  - `preschool`: Foreign key to Preschool
  - `classroom`: Foreign key to Classroom (optional)
  - `is_equipment_request`: Boolean flag
  - `is_training_request`: Boolean flag
  - `status`: open, in_progress, closed, resolved
  - `priority`: low, medium, high, urgent
  - `resolution_note`: Admin notes
  - `created_at`, `updated_at`, `resolved_at`: Timestamps

#### SupportTicketItem Model
- **Fields:**
  - `id` (UUID): Primary key
  - `ticket`: Foreign key to SupportTicket
  - `item_type`: Type of support request (10 equipment + 1 training options)
  - `details`: Text details from user
  - `preferred_format`: For training requests (hadau hadap malu, vídeo guia, etc.)
  - `app_features_to_learn`: For training requests

### Support Request Types

#### Equipment Support (Items 1-10)
1. Troka lâmpada projetor (Projector lamp replacement)
2. Ajuda atu halo konfigurasaun Miracast (Miracast configuration help)
3. Suporta projetor – hadia ka troka (Projector support - repair/replace)
4. Tela klen – problema (Screen problem)
5. Tablet – problema tékniku (Tablet technical problem)
6. Tablet – na'ok (Tablet lost)
7. Tablet – estragu (Tablet damaged)
8. Projetor – estragu ka la funsiona (Projector damaged/non-functional)
9. Problema ho kabelu ka adaptador (Cable/adapter problem)
10. Problema seluk ho ekipamentu AV (Other AV equipment problems)

#### Training/Professional Development (Item 11)
11. Husu formasaun jerál (General training request)
    - Preferred format (e.g., in-person, video guide, workshop, 1:1)
    - App features to learn (e.g., navigation, configuration, class management)

### Views

#### SupportTicketCreateView
- Teacher only access
- Step 1: Create ticket with classroom (optional) and priority
- Redirects to add items

#### SupportTicketAddItemsView
- Step 2: Select request types and add details
- Teachers can select multiple equipment items
- Teachers can select training requests
- Validates at least one item is selected

#### SupportTicketListView
- Teachers see only their own tickets
- Admins see all tickets
- Filtering by status and ticket number
- Pagination: 20 items per page

#### SupportTicketDetailView
- View ticket details and items
- Teachers see their own tickets
- Admins see all tickets

#### SupportTicketUpdateView
- Admin only access
- Update status, priority, and resolution notes
- Auto-sets resolved_at timestamp

### Forms

#### SupportTicketForm
- Classroom selection (optional)
- Priority selection

#### SupportTicketItemForm
- Item type selection
- Details text area
- Training-specific fields (preferred_format, app_features_to_learn)

### URLs

```
/ticket/create/ - Create new support ticket
/ticket/<uuid:pk>/items/ - Add items to ticket
/ticket/<uuid:pk>/ - View ticket details
/ticket/<uuid:pk>/update/ - Update ticket status (admin)
/ticket/list/ - List tickets
/ticket/ajax/get-by-number/ - Get ticket by number (AJAX)
```

### Templates

- `templates/ticket/support_ticket_form.html` - Create ticket form
- `templates/ticket/support_ticket_items_form.html` - Add items form
- `templates/ticket/support_ticket_detail.html` - View ticket details
- `templates/ticket/support_ticket_list.html` - List tickets with filters
- `templates/ticket/support_ticket_update.html` - Admin update form

---

## 4. Admin Panel

### Equipment Admin (`equipment/admin.py`)
- **EquipmentAdmin**: Manage equipment records
  - List view with filters (type, status, preschool, date)
  - Search by serial number or model
  - Inline editing

- **EquipmentAssignmentHistoryAdmin**: View assignment changes
  - Filtered by date
  - Searchable by serial number or reason

### Ticket Admin (`ticket/admin.py`)
- **SupportTicketAdmin**: Manage support tickets
  - List view with filters (status, priority, type, date)
  - Search by ticket number or teacher
  - Inline items editing

- **SupportTicketItemAdmin**: View ticket items
  - Filtered by type
  - Searchable by ticket number

---

## 5. Security & Access Control

### Equipment Views
- `AdminOnlyMixin`: Restricts equipment management to MoE admins
- Equipment cannot be modified by non-admins

### Support Ticket Views
- `TeacherOnlyMixin`: Restricts ticket creation to teachers
- Teachers can only view their own tickets
- Admins can view all tickets and update status

---

## 6. Database Migrations

Required migrations:
1. Create Equipment model with enhanced fields
2. Create EquipmentAssignmentHistory model
3. Create SupportTicket model with new fields
4. Create SupportTicketItem model

Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 7. Frontend Features

### Equipment Management
- Dynamic classroom dropdown (filtered by preschool)
- AJAX-based classroom loading
- Assignment history table
- Status-based color coding
- Search and filtering interface
- Bulk action buttons

### Support Ticket Form
- Conditional visibility of details input
- Separate sections for equipment and training
- Interactive checkbox-based item selection
- Form validation (at least one item required)
- Auto-generated unique ticket numbers
- Real-time form validation

---

## 8. API Endpoints

### AJAX Endpoints
- `/equipment/ajax/load-classrooms/` - Get classrooms for preschool
- `/ticket/ajax/get-by-number/` - Get ticket details by number

---

## 9. Usage Examples

### Creating Equipment
1. Admin navigates to `/equipment/add/`
2. Fills in equipment details
3. Selects preschool (classroom dropdown auto-populates)
4. Optionally assigns to teacher
5. Submits form

### Changing Equipment Assignment
1. Admin navigates to equipment detail page
2. Clicks "Change Assignment" button
3. Selects action (reassign/delete/retire)
4. For reassign: selects new preschool and optionally classroom/teacher
5. Adds reason for change
6. Submits form
7. Assignment history is automatically updated

### Creating Support Ticket
1. Teacher navigates to `/ticket/create/`
2. Selects classroom (optional) and priority
3. System creates ticket with auto-generated number
4. Redirects to `/ticket/<id>/items/`
5. Teacher selects equipment issues and/or training requests
6. For each selected item, can add details
7. For training requests, can specify format and features
8. Submits form
9. Ticket is created and visible in dashboard

### Viewing Support Tickets
- Teachers: Go to `/ticket/list/` to see their own tickets
- Admins: See all tickets with status overview
- Can filter by status and ticket number
- Click on ticket to view full details and items

---

## 10. Notes for Developers

### Important Database Fields
- Equipment.serial_number is UNIQUE - prevents duplicates
- SupportTicket.ticket_number is auto-generated and UNIQUE
- EquipmentAssignmentHistory tracks all changes for audit trail

### Permissions
- Only MoE admins can manage equipment
- Only teachers can create support tickets
- Only admins can resolve/update ticket status

### Localization
- All user-facing text in Tetun language
- Form labels and button text in Tetun
- Admin panel mostly in English

---

## 11. Future Enhancements

Potential improvements:
- Barcode/QR code scanning for equipment
- Equipment condition ratings
- Automated ticket assignment to support team
- Email notifications for ticket updates
- Dashboard widgets showing equipment status
- Monthly reports on equipment and support tickets
- Integration with budget/procurement system

---

## 12. Troubleshooting

### Issue: Classroom dropdown not populating
- Ensure preschool is selected first
- Check JavaScript console for errors
- Verify AJAX endpoint is working

### Issue: Equipment serial number duplicates
- Serial number field is unique
- Check existing equipment before creating new record

### Issue: Ticket number not generating
- Ensure ticket model migration is applied
- Check random module is available

### Issue: Teacher can't see equipment
- Equipment must be assigned to teacher's classroom
- Verify teacher role is correct in User model

---

## 13. Related Files

### Models
- `equipment/models.py` - Equipment and history models
- `ticket/models.py` - Support ticket models

### Views
- `equipment/views.py` - Equipment views
- `ticket/views.py` - Support ticket views

### Forms
- `equipment/forms.py` - Equipment forms
- `ticket/forms.py` - Support ticket forms

### URLs
- `equipment/urls.py` - Equipment routes
- `ticket/urls.py` - Support ticket routes
- `haap_platform/urls.py` - Main URL configuration

### Templates
- `templates/equipment/` - Equipment templates
- `templates/ticket/` - Support ticket templates

### Admin
- `equipment/admin.py` - Equipment admin
- `ticket/admin.py` - Support ticket admin

---

## 14. Deployment Checklist

- [ ] Apply migrations: `python manage.py migrate`
- [ ] Create superuser if needed
- [ ] Test equipment creation flow
- [ ] Test support ticket creation flow
- [ ] Verify admin panel works
- [ ] Test AJAX endpoints
- [ ] Check permission restrictions
- [ ] Verify emails (if implemented)
- [ ] Test on mobile devices
- [ ] Review security measures

---

**Implementation Date**: May 30, 2026
**Django Version**: 3.2+
**Python Version**: 3.8+
