# Yoga Class: An online yoga class booking and management system
#### Video Demo: https://youtu.be/VyFltnfi2nY
#### Description:

# Background

## Situation

This project is created with the inspiration from my friend, who is working as a freelance yoga instructors. She mainly teaches small group class (around two to four persons) and, sometimes, one-to-one private classes. Therefore, her classes are full quite quickly when the classes are scheduled. She teaches several different types of yoga e.g. relaxing stretch, sleeping yoga, etc. As she is not able to afford to own / rent her own yoga studio, she books yoga venues of different places in Hong Kong e.g. Kwun Tong, Tsim Sha Tsui, etc. Currently, she uses an Instagram page to release information about her yoga classes to potential students.

## Difficulties

While Instagram is popular and can easily attract more potential students, it is not a very good tool to organise and systematically release detailed, up-to-date information to readers. It leads to a large amount of customer service tasks to provide more information to potential students. For example, she often needs to answer enquiries about whether there are still places available in a particular yoga class, whether she is free to organise an one-to-one private class at a particular timeslot, etc. She also needs to handle all booking requests and input all the information into a spreadsheet herself. While this is a good trend as her yoga classes are getting more popular, she is increasingly busy with the administrative work as she cannot afford to hire a clerk or an assistant.

# Design Overview

## Tasks to be handled

In light of the current difficulties, this web application developed with flask is largely an online yoga class booking and management system. Although it cannot eliminate all the administrative work (to be explained why below), it can make many of the current work procedures automated.

The major tasks that this web application handles include:
- allowing my friend (or her partners / staff in future!) to add new yoga classes and edit information about them;
- allowing potential students to check class timetable and, more importantly, number of places available;
- allowing potential students to understand briefly the time slots that private classes can be organised;
- allowing potential students to make bookings; and
- allowing my friend to confirm bookings after payment is received.

## No online payment system

As the later part of this document will show, there is no online payment system plugged into this web application. It means that students need to make payments on their own, send the receipts to my friend, and my friend need to check on her own whether the payment amounts are correct (so as to confirm the bookings). It is because the more automated online payment systems (e.g. the one that can check the payment amount) usually involve transaction cost or service charge, something that the small-scale freelancing business cannot afford. While administrative tasks are still there, the burden is already much lessened.

## More about this web application

This web application relies on `layout.html` as an anchor to show information of all other HTML pages. Thanks to the latest Bootstrap (version 5.0.1), it can be a responsive one, being more mobile-friendly. When writing the HTML pages with table(s), number of columns is limited so as to allow users to obtain information and use the booking platform with their smartphones more easily.

In the paragraphs below, more information about the design of this web application will be explained. It starts with how user accounts are managed. Then, how the timetable is created and bookings are handled will be explained. Finally, some more static parts e.g. "About Us" will be discussed briefly as well.

# Accounts

## Create account

While it is not necessary to have an account to view class timetable, account is still required to make bookings. When the user goes to "Create Account" in the navbar, the function `create()` in `application.py` is called. When the user fills in and submit the form in `create.html`, the information will be "POSTed" and `create()` will handle the work. One important step is that, in the database `yogaclass.db` that is handled with SQLite, a table called `accounts` is created if not yet done before. This table saves all the users' account information. Certainly, it is too dangerous to save users' passwords as plaintexts - therefore, `werkzeug.security` is imported to hash the password so that the administrators of this web application also cannot know what the users' passwords are.

It should be noted that, in this `accounts` table, the very first row (with `id = 1`) is the administrator's accounts. When logged in with this accounts, more functions about adding classes, managing bookings, etc. are available. More about this will be discussed below.

## Log in

After the account is created, the user can log in so as to make and check bookings. The function `login()` is called, and Session imported from flask_session is used here to maintain the login status.

## Manage account

It is normal for users to want to change their email address, phone numbers and passwords. When they go to "My Account" in the navbar about logging in, the function `myaccount()` is called. A form in `myaccount.html` is shown and users can "POST" the new information that they want to change. `myaccount()` will then handle the information and update the `accounts` table in the database.

## Forgetting password

When a user forgets her/his password, her/his registered email address is important. First, the user's identity is checked by entering her/his email address. In `forgetpw()`, \*flask_mail\* module is then utilised to send an email. The email is formatted in \*reset_pw.html\*. It is too dangerous to send the password to the user directly in the email; in fact, it is also impossible to do so as the passwords are hashed. Therefore, the user will just be allowed to re-create a new password by clicking the link that call `resetpw()`, which in fact allows the user to access `resetpw.html`.

In this HTML page, the user is provided with a form to "POST" new password information. To play safe, the user is also required to enter a security code, which is actually a five-digit integer randomly generated and sent in the email. The user's ID and this security code are saved in a table called `resetpw`; whether the security code is correct or not is checked with the help of this table. This is to prevent the situation in which someone tries to access `resetpw.html` directly by typing the URL - this person may maliciously change the password of someone else. Certainly, the assumption here is that the email account of the user is secured!

When the new password information is "POSTed" and the password is hashed, the `accounts` table is updated. All the rows with the user's ID in `resetpw` table are dropped, so as to prevent any re-use of the security code by this user in near future.

## Log out

When the user clicks "Log Out" in the navbar, `logout()` is called. Simply speaking, the user is then logged out.

# Timetable and Bookings

## Timetable

A key feature of this application is to allow the administrator to update timetable and the potential students to read class information. When the administrator is logged in, a special navbar is available that allows her/him to click "Add Class". The function `addclass()` is then called and `addclass.html` is then shown. However, when someone not logged in as the administrator attempts to go to the HTML page directly, s/he will be rejected and asked to log in as administrator.

In `addclass.html`, a form is available for the administrator to input information of a new class, or a timeslot that the yoga instructor is available for private classes. When submitted, the information is "POSTed" to `addclass()`. A new table, `timetable`, is then created in the database if it does not exist. This table stores all the information about the classes.

When anyone clicks "Class Timetable" in the navbar, s/he sees a table in which the information is recalled from this `timetable` table. However, when viewing the class timetable, the user can only see classes that are held later than today. On the one hand, it is not necessary to let users read information of past classes; on the other hand, it is not desirable to overwhelm the users with tonnes amount of information when more yoga classes are organised. To achieve this, the datetime module is utilised. Moreover, it is important to import timezone and timedelta so as to adjust all time to be local Hong Kong time (GMT+8).

When a user views the class timetable at the first glance, only limited information i.e. data, time, class type and location are available. As mentioned above, it is important to limit the number of columns of an HTML table so as to make the web application more mobile-friendly. The user can click the "Info" button to see more detailed information about the class e.g. class size, place(s) available, price, etc. When there is no places available, it will show that the class is full (in red); otherwise, there will be a HTML form with a select bar and a submit button. The select bar allows the user to make a booking depending on the number of places available. (A user can make booking for more than one places, because sometimes a user's friend may want to join just one class to have a taste first.)

## Bookings

When the user clicks "Submit", the information about this class and the number of place(s) to book will be "POSTed" to the function `timetable()`. This function then return all the information to another HTML form in another HTML page called `confirmbooking.html`. The purpose of this page is just to allow users to check the booking information - therefore, most blanks in the form are given the attribute `readonly`. Then, when the user confirms the information and submits the form again, the information is "POSTed" to the function `confirmbooking()`. In this function, another table called `bookings` is created to store all the information of each booking.

After the function `confirmbooking()` updates the `bookings` table, the user is directed to another HTML page called `mybookings.html`. Two tables can be viewed in this page - one showing upcoming bookings, another one showing past bookings. The booking just made, together with a booking ID (the primary key in the `bookings` table), is shown in the former table. The user needs to pay attention to the status of the booking - it is always "Pending" immediately after the booking is made, which means that the booking is not confirmed and the user needs to make payment. The payment methods can be found in the "Payment" of the navbar.

Supposedly, the user needs to make payment within ten hours and send the payment proof with the unique booking ID to the yoga instructor through Signal or Whatsapp. Then, when the payment is correct, the administrator can use her/his account to manually change the status of the booking from "Pending" to "Confirmed". In case the user refuses to make any payment, the administrator can change the status to "Cancelled", and other users can see more place(s) available again in Class Timetable because it also changes the information in the `timetable` table (pay attention to the column `place_free`).

# Static Pages

The web application also include some more static pages that include more stable information related to the yoga classes. In `aboutus.html`, which can be accessed by clicking "About Us", users can read the qualifications of the yoga instructor and some basic information about different types of yoga classes. The information here can certainly be enriched because, in fact, the one developing this web application is not a yoga person.

Another page, `payment.html`, is mentioned above. It includes the three payment methods available to the students. Please note that while QR codes can allow more convenient payments through FPS and PayMe (some payment methods commonly used in Hong Kong), the read QR code images are not given in this project to avoid unncessary and accidental money transfer.

# Future Development

Perhaps it has already been noted that, when a user creates an account, other than contact information, other information like gender and year of birth is also collected. Hopefully, in future, the administrator can make use of this information to more systematically analyse the profile of students of a particular class type / time / location. Certainly, allowing a user to make booking for someone else (because a user can book for more than one place in a class) damages the accuracy of the profile, but the data should still have some referencing value.

More programatically, it is hoped that the auto-email system can be strengthened so that the users can receive email notifications when one of their booking status (initially "Pending") is changed. In longer term, it is also hoped that registered users can receive email notifications when new classes are added, or when an originally full class becomes available again!

This is Yoga Class!