# Django Contact API

This is a simple API to view and manage the contact list of the Django User default. These are the minimum requirements:
- A single user might have one or multiple contacts on their contact list
- A single contact might have one or multiple phone numbers
- A single user might have one or multiple groups on their contact list
- A single contact group can have one or multiple contacts

## Entity Relationship Diagram
<br/>

<p align = "center">
<img src="https://user-images.githubusercontent.com/21379421/172562459-f4e8370e-fd92-4a71-b713-0973fe488a6c.png">
</p>
<p align = "center">
<b><i>Figure 1 - Entity relationship between (Contact, Phone) and (Contact, Contact Membership)</i></b>
</p>

---

<p align = "center">
<img src="https://user-images.githubusercontent.com/21379421/172562482-efd321a6-0eeb-4da2-8720-82a26f1449dc.png">
</p>
<p align = "center">
<b><i>Figure 2 - Entity relationship between (Contact, Group) and (Group, Group Membership)</i></b>
</p>

## How to run the test project
- Open your terminal.
- Navigate to the `django-contact` directory.
- Setup python [virtual environment](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments) and then activate it.
- Run `./scripts/run-project.sh`

# API Design
This section describes endpoint designs that are applicable for users with a specific access level.

## Authenticated User
### Contacts
- `GET /contacts/`: Get all contacts.

## Admin
### Contacts
- `POST /contacts/`: Create a new contact.<br/>
  **Request Body**
  ```
   {
      "user": 1,
      "nickname": "",
      "company": "",
      "title": "",
      "address": ""
   }
  ```
- `GET /contacts/<int:id>/`: Retrieve contact with specific ID.
- `UPDATE /contacts/<int:id>/`: Update contact with specific ID.<br/>
  **Request Body**
  ```
   {
      "nickname": "",
      "company": "",
      "title": "",
      "address": ""
   }
  ```
- `DELETE /contacts/<int:id>/`: Delete contact with specific ID.

### Phone numbers
- `POST /contacts/<int:contact_id>/phone-numbers/`: Create a new phone number for the given contact ID.<br/>
  **Request Body**
  ```
   {
      "phone_number": "+6281222333444",
      "phone_type": "cellphone" | "telephone" | "telefax",
      "is_primary": true
   }
  ```
- `UPDATE /contacts/<int:contact_id>/phone-numbers/<int:id>/`: Update phone number of the given contact ID.<br/>
  **Request Body**
  ```
   {
      "phone_number": "+6281222333444",
      "phone_type": "cellphone" | "telephone" | "telefax",
      "is_primary": true
   }
  ```
- `DELETE /contacts/<int:contact_id>/phone-numbers/<int:id>/`: Delete phone number of the given contact ID.

## User
### Contact Membership
- `GET /contacts/me/contacts/`: Get contact list belongs to the requester's contact list.
- `POST /contacts/me/contacts/`: Create a new contact in the requester's contact list.<br/>
  **Request Body**
  ```
   {
      "contact": 1,
      "starred": true | false
   }
  ```
- `GET /contacts/me/contacts/<int:contact_id>/`:  Retrieve contact from the requester's contact list.
- `DELETE /contacts/me/contacts/<int:contact_id>/`:  Delete new contact from the requester's contact list.

### Contact Groups
- `GET /groups/`: Get contact groups that are accessible to the requester.
- `POST /groups/`: Create a new contact group.<br/>
  **Request Body**
  ```
   {
      "name": "",
      "description": ""
   }
  ```
- `GET /groups/<int:id>/`: Retrieve contact group with specific ID.
- `UPDATE /groups/<int:id>/`: Update contact group with specific ID.<br/>
  **Request Body**
  ```
   {
      "name": "",
      "description": ""
   }
  ```
- `DELETE /groups/<int:id>/`: Delete contact group with specific ID.

### Contact Group Membership
- `GET /groups/<int:group_id>/contacts/`: Get contact list in the given group ID.
- `POST /groups/<int:group_id>/contacts/`: Add contact to the given contact group ID.<br/>
  **Request Body**
  ```
   {
      "contact": 1,
      "role": "admin" | "member",
      "inviter": 1
   }
  ```
- `GET /groups/<int:group_id>/contacts/<int:id>/`: Retrieve contact from the given contact group ID.
- `PUT /groups/<int:group_id>/contacts/<int:id>/`: Update contact in the given contact group ID.<br/>
  **Request Body**
  ```
   {
      "role": "admin" | "member"
   }
  ```
- `DELETE /groups/<int:group_id>/contacts/<int:id>/`: Delete contact from the given contact group ID.
