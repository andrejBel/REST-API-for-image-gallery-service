## API DOCUMENTATION (Paths)

### images/

**GET**

Get all public images for anonymous and normal user, for admin get all images.

*Codes*
- 200 OK

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| page          | Integer   | False         | Defines which page to return  |
| page_size     | Integer   | False         | Defines the size of one page  |
| anonymous     | Boolean   | False         | Whether to display anonymous images   |
| username      | String    | False         | Defines the name of the user whose images to view  |
| user_id       | Integer   | False         | Defines the id of the user whose images to view  |

*Output format*

```
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 2,
            "created_at": "2020-03-29T08:08:04.810458Z",
            "title": "myimage1.jpg",
            "description": "popis",
            "file": null,
            "public": true,
            "comment_count": 0,
            "upvote_count": 0,
            "downvote_count": 0,
            "favourite_count": 0,
            "report_count": 0
        },
        ...
    ]
}
```

**POST**

Add image. Anonymous user can add only public images. The uploader is the owner of image.

*Codes*
- 200 OK
- 400 Bad request 

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| title         | String    | False         | Title of the images to upload |
| description   | String    | False         | Description of the image      |
| public        | Boolean   | False         | Whether the image is public   |
| file          | ImageFile | True          | The file to upload            |

---

### images/:id

**GET**

Get details for image with :id - comments, favourites and votes. If image is public, it is visible for everyone, otherwise only for owner and admin

*Codes*
- 200 OK
- 401 Unauthorized
- 403 Permission denied
- 404 Image not found

*Output format*

```
"id": 1,
    "user": 2,
    "created_at": "2020-04-23T12:14:37.117390Z",
    "title": "myimage1.jpg",
    "description": "popis",
    "public": true,
    "file": "http://localhost:9001/django-media/myimage1.jpg",
    "comments": [
        {
            "id": 1,
            "image": 1,
            "user": 2,
            "created_at": "2020-04-23T12:14:37.377065Z",
            "comment_text": "text 1"
        },
        ... 
    ],
    "votes": [
        {
            "id": 1,
            "image": 1,
            "user": 2,
            "upvote": true,
            "created_at": "2020-04-23T12:14:37.390257Z"
        },
        ...
    ],
    "favourites": [
        {
            "id": 1,
            "image": 1,
            "user": 2
        },
        ...
    ],
    "reports": []
}
```

**PUT**

Update image with :id. Current user has to be the owner of the image or admin to call PUT.

*Codes*
- 201 Created
- 400 Bad request
- 401 Unauthorized
- 403 Permission denied
- 404 Image not found

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| title         | String    | False         | New title of the image        |
| description   | String    | False         | New description of the image  |
| public        | Boolean   | False         | New accessibility of the image |

**DELETE**

Delete image with :id. Current user has to be the owner of the image or admin.

*Codes*
- 204 Image deleted
- 403 Permission denied
- 404 image not found

---

### images/:id/comment

**GET**

Get a list of comments for image with :id. For public image all can view, for private only owner and admin can list comments.

*Codes*
- 200 OK
- 404 Image not found

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| page          | Integer   | False         | Defines which page to return  |
| page_size     | Integer   | False         | Defines the size of one page  |

*Output format*

```
{    
    "count": 4,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "image": 1,
            "user": 2,
            "created_at": "2020-04-23T12:14:37.377065Z",
            "comment_text": "text 1"
        },
        ...
    ]
}
```

**POST**

Add new comment to image. User has to be authenticated to comment. If the image is public, every user can comment, otherwise only owner and admin can.

*Codes*
- 201 OK
- 400 Bad request
- 403 Permission denied

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| comment_text  | String    | True          | Text of the comment           |

---

### images/:id/report

**GET**

Get a list of all reports for image with :id. Only owner and admin can list reports. If owner of the image is anonymous, then everyone can see reports.

*Codes*
- 200 OK
- 404 Image not found

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| page          | Integer   | False         | Defines which page to return  |
| page_size     | Integer   | False         | Defines the size of one page  |

*Output format*

```
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 0,
      "image": 0,
      "user": 0,
      "comment": "string",
      "created_at": "2020-04-27T10:07:57.816Z"
    }
  ]
}
```

**POST**

Report an image. Everyone can report public images while only admin and owner can report private ones.

*Codes*
- 201 OK
- 400 Bad request
- 403 Permission denied

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| comment       | String    | False         | Additional comment for the report |

---

### images/:id/vote

**PUT**

Vote on an image. Type of vote = 'up', 'down', 'undo'. User has to be authenticated. If image is public, every user can vote, otherwise only owner and admin 

*Codes*
- 201 Message success
- 400 Bad request
- 401 Unauthorized
- 403 Permission denied
- 404 Image not found

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| type          | String    | True          | Type of the vote. Can be 'up', 'down' or 'undo' |

---

### images/:id/favourite

**PUT**

Add or remove images from favourites. Everyone can add public image, only admin and owner can add private. User has to be authenticated. Type = 'add' or 'remove'

*Codes*
- 201 Message success
- 400 Bad request
- 403 Permission denied
- 404 Image not found
 
*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| type          | String    | True          | Type of the action. Can be 'add' or 'remove' |

---

### images/trending

**GET**

Get all public images sorted by number of votes in last 24 hours.

*Codes*
- 200 OK

Output format and parameters are identical with GET images/

---

### me/images

**GET**

Get images of current user. User has to be authenticated. Allows for many filters.

*Codes*
- 200 OK
- 401 Unauthorized
- 403 Permission denied

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| page          | Integer   | False         | Defines which page to return  |
| page_size     | Integer   | False         | Defines the size of one page  |
| visibility    | Boolean   | False         | Whether to return public or private images  |

Output format is identical to GET images/

---

### me/images/voted

**GET**

Get images which current user has voted on. User has to be authenticated. Filter for up/down votes. 

*Codes*
- 200 OK
- 401 Unauthorized
- 403 Permission denied

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| page          | Integer   | False         | Defines which page to return  |
| page_size     | Integer   | False         | Defines the size of one page  |
| voted         | String    | False         | Values 'up' or 'down. Whether to list images where voted is up/down  |

Output format is the same as GET images/

---

### me/images/favourites

**GET**

Get favourite images of current user. User has to be authenticated.

*Codes*
- 200 OK
- 401 Unauthorized
- 403 Permission denied

Output format and parameters are the same as GET images/

---

### me/images/favourites/download

**GET**

Download favourite images of user in *.zip. User has to be authenticated.

*Codes*
- 200 HttpResponse with downloadable content
- 403 Permission denied

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| name          | String    | True          | Resulting name of the zip file (default is 'favourites') |

---

### comment/:id

**PUT**

Update comment. User has to be authenticated. If comment is on public image, owner of comment, owner of image and admin can edit. Otherwise only owner of image and admin can. Returns updated comment.

*Codes*
- 201 Created
- 400 Bad request
- 403 Permission denied
- 404 Not found

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| comment_text  | String    | True          | New text of the comment       |

*Output format*

```
{
  "id": 0,
  "image": 0,
  "user": 0,
  "created_at": "2020-04-27T10:18:04.446Z",
  "comment_text": "string"
}
```

**DELETE**

Delete comment. User has to be authenticated. If comment is on public image, owner of comment, owner of image and admin can edit. Otherwise only owner of image and admin can.

*Codes*
- 204 No content
- 403 Permission denied
- 404 Not found

---

### users/

**GET**

List of all users. Only for admin

*Codes*
- 200 OK
- 403 Permission denied

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| page          | Integer   | False         | Defines which page to return  |
| page_size     | Integer   | False         | Defines the size of one page  |

*Output format*

```
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 0,
      "username": "string",
      "images": [
        {
          "id": 0,
          "user": 0,
          ...
          "comments": [ ... ],
          "votes": [ ... ],
          "favourites": [ ... ],
          "reports": [ ... ]
        }
      ],
      "comments": [ ... ],
      "votes": [ ... ],
      "favourites": [ ... ]
    }
  ]
}
```

---

### users/:id

**GET**

Detail of one user with :id. Only for admin

*Codes*
- 200 OK
- 403 Permission denied

Output format is identical with GET users/, only the pagination header is missing and the response is for one user only.

---

### register/

**POST**

Registers new user, returns token.

*Codes*
- 201 Created
- 400 Validation errors
- 401 Unauthorized

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| username      | String    | True          | Username for the new user     |
| password      | String    | True          | Password for the new user     |
| email         | String    | True          | E-mail for the new user       |

*Output format*

```
[
  {
    "id": 0,
    "username": "string",
    "email": "user@example.com",
    "token": "string"
  }
]
```

---

### me/profile

**PUT**

Change details about user who is authenticated.

*Codes*
- 201 Created
- 400 Bad request
- 401 Unauthorized

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| current_password | String    | True          | Current password of the user |
| new_password  | String    | True          | New password for the user     |
| email         | String    | True          | An e-mail of the user         |

*Output format*

```
{
  "id": 0,
  "username": "string",
  "email": "user@example.com"
}
```

---

### login/

**POST**

Log user in, returns token.

*Codes*
- 200 OK
- 400 Validation errors
- 404 Invalid credentials

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| username      | String    | True          | Username for the user to log in |
| password      | String    | True          | Password of the user          |

*Output format*

```
[
  {
    "id": 0,
    "username": "string",
    "email": "user@example.com",
    "token": "string"
  }
]
```

---

### login/:backend

**POST**

Log in user using social login. Returns token. :backend = 'facebook' or 'google-oauth2'. <br>
Exchange an OAuth2 access token for one for this site.
This simply defers the entire OAuth2 process to the front end.
The front end becomes responsible for handling the entirety of the
OAuth2 process; we just step in at the end and use the access token to populate some user identity.

*Codes*
- 201 OK
- 400 Bad request

*Parameters*

| Name          | Type      | Required      | Description                   |
|---------------|-----------|---------------|-------------------------------|
| access_token  | String    | True          | Access token for the authentication backend |

*Output format*

```
{
  "id": 0,
  "username": "string",
  "email": "user@example.com",
  "token": "string"
}
```

---

### logout/

**GET**

Log user out.

*Codes*
- 200 User logged out
- 401 Unauthorized

----------------------------------------------------------


## USERS

**3 user levels**
- Anonymous
- Normal
    - Authenticated - does not own the object of interest
    - Owner - user who owns the objects, who posted it - either image or comments
- Admin - the god of the system

**2 authentication states**
- Anonymous
- Authenticated