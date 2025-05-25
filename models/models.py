from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, password, first_name, surname, postcode, mobile_number, email,
                 previous_job_title=None, previous_company=None, previous_job_description=None):
        self.id = id
        self.username = username
        self.password = password
        self.first_name = first_name
        self.surname = surname
        self.postcode = postcode
        self.mobile_number = mobile_number
        self.email = email
        self.previous_job_title = previous_job_title
        self.previous_company = previous_company
        self.previous_job_description = previous_job_description
        self.email_validated = False
