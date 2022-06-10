# Django Contact API

This is a simple API to view and manage the contact list of the Django User default. These are the minimum requirements:
- A single user might have one or multiple contacts on their contact list
- A single contact might have one or multiple phone numbers
- A single user might have one or multiple groups on their contact list
- A single contact group can have one or multiple contacts

## Entity Relationship Diagram
<br/>

<p align = "center">
<img src="https://user-images.githubusercontent.com/21379421/172641711-ffa80bbc-0e89-481d-ba0d-81f602394cbe.png">
</p>
<p align = "center">
<b><i>Figure 1 - Contact-to-Contact relationship</i></b>
</p>

---
<br/><br/>

<p align = "center">
<img src="https://user-images.githubusercontent.com/21379421/172641745-ef3005d0-965d-46d2-8600-6cd723ac1839.png">
</p>
<p align = "center">
<b><i>Figure 2 - Contact-to-Phone relationship</i></b>
</p>

---
<br/>

<p align = "center">
<img src="https://user-images.githubusercontent.com/21379421/172641797-5b73dfcc-ac64-4fdf-a757-943deb4f64fe.png">
</p>
<p align = "center">
<b><i>Figure 3 - Contact-to-Group Relationship</i></b>
</p>

## How to run the test project
- Open your terminal.
- Navigate to the `django-contact` directory.
- Setup python [virtual environment](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments) and then activate it.
- Copy-paste `/scripts/.env.sh.template` in the same directory, and then rename it as `.env.sh`.
- Modify the IP Address of your local `SERVER` and its `PORT` number when necessary.
- Run `./scripts/run-project.sh`

# API Design
This section describes endpoint designs that are applicable for users with a specific access level.

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

## Authenticated User
### Contacts
- `GET /contacts/`: Get all contacts.<br/>
  **Response**
  ```
   [
     {
        "id": 1,
        "first_name": "User",
        "last_name": "One",
        "nickname": "",
        "email": "user1@mail.com",
        "company": "",
        "title": "",
        "phone_numbers": [
            {
                "id": 1,
                "phone_number": {
                    "value": 81222333444,
                    "country_code": 62,
                    "country_code_source": 1
                },
                "type": "cellphone",
                "is_primary": true,
                "created_at": "2022-06-08T07:18:28.477549Z",
                "updated_at": "2022-06-08T07:18:28.477581Z"
            }
        ],
        "address": "",
        "created_at": "2022-06-08T07:17:11.255513Z",
        "updated_at": "2022-06-08T07:17:11.255548Z"
     }
   ]
  ```

### Contact Membership
- `GET /contacts/me/contacts/`: Get contact list belongs to the requester's contact list.<br/>
  **Response**
  ```
   [
     {
        "id": 1,
        "first_name": "User",
        "last_name": "One",
        "nickname": "",
        "email": "user1@mail.com",
        "company": "",
        "title": "",
        "phone_numbers": [
            {
                "id": 1,
                "phone_number": {
                    "value": 81222333444,
                    "country_code": 62,
                    "country_code_source": 1
                },
                "type": "cellphone",
                "is_primary": true,
                "created_at": "2022-06-08T07:18:28.477549Z",
                "updated_at": "2022-06-08T07:18:28.477581Z"
            }
        ],
        "address": "",
        "starred": false,
        "created_at": "2022-06-08T07:17:11.255513Z",
        "updated_at": "2022-06-08T07:17:11.255548Z"
     }
   ]
  ```
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
- `GET /groups/`: Get contact groups that are accessible to the requester.<br/>
  **Response**
  ```
   [
     {
        "id": 1,
        "name": "Test Group",
        "description": "Description update",
        "created_by": 1,
        "created_at": "2022-06-08T07:21:16.195551Z",
        "updated_by": 1,
        "updated_at": "2022-06-10T02:50:08.397982Z"
     }
   ]
  ```
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
- `GET /groups/<int:group_id>/contacts/`: Get contact list in the given group ID.<br/>
  **Response**
  ```
   [
     {
        "id": 1,
        "first_name": "User",
        "last_name": "One",
        "nickname": "",
        "email": "user1@mail.com",
        "company": "",
        "title": "",
        "phone_numbers": [
            {
                "id": 1,
                "phone_number": {
                    "value": 81222333444,
                    "country_code": 62,
                    "country_code_source": 1
                },
                "type": "cellphone",
                "is_primary": true,
                "created_at": "2022-06-08T07:18:28.477549Z",
                "updated_at": "2022-06-08T07:18:28.477581Z"
            }
        ],
        "address": "",
        "created_at": "2022-06-08T07:17:11.255513Z",
        "updated_at": "2022-06-08T07:17:11.255548Z"
     }
   ]
  ```
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
