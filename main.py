from bs4 import BeautifulSoup
import requests
import re


class Course:
    def __init__(self, code: str, crosslisted: bool):
        self.code = code
        self.crosslisted = crosslisted
        self.crossclasses = []

    def __str__(self):
        if not self.crosslisted:
            return self.code

        string = self.code
        for code in self.crossclasses:
            string = "%s / %s" % (string, code)
        return string


def find_course(courses, code):
    index = 0
    while index < len(courses) and courses[index].code != code:
        index += 1
    if index == len(courses):
        return -1
    return index


def can_remove_section(code):
    # Return true unless course code is 194, 294, 394, or 494.
    # Different sections of courses with these codes are often
    # completely different classes altogether
    return code.find("494") == -1 and code.find("394") == -1 and code.find("294") == -1 and code.find("194") == -1


# Fetch the registrar's current course schedule page for Spring 2020
url = requests.get(
    "https://www.macalester.edu/registrar/schedules/2020spring/class-schedule/")
html = url.text

# Parse entire HTML doc
soup = BeautifulSoup(html, "html.parser")

# Get the children of the lowest common ancestor of all relevant data elements
container = soup.find(id="completeSchedule")
sections = container.find_all("div", class_="class-schedule-wrapper")

courses = []
index = -1

# Iterate through each section
for section in sections:
    # Each section only has one table, and its body is the only important part
    body = section.table.tbody

    # Get all the rows that contain the course code
    rows = body.find_all("tr", attrs={"data-id": True})

    # Iterate through every course code row
    for row in rows:
        # Get details string that contains cross-list info
        details = row.next_sibling.next_sibling.td.p.string
        if details is None:
            details = ""

        # Determine whether the current course is cross-listed
        crosslisted = details.find("ross-listed with ") != -1

        # Get the course code in the current row
        code = row.find("td", class_="class-schedule-course-number").string

        # Remove section number from course code (except for 194 and 294 courses)
        if can_remove_section(code):
            code = code.split("-")[0]

        # Avoid duplicate course entries
        if index != -1:
            if courses[index].code == code:
                continue

        course = Course(code, crosslisted)
        if crosslisted:
            # Find first cross-listed course code
            match = re.search(
                "(?<=ross-listed with )([A-Z]* [0-9]*-[A-Z0-9][A-Z0-9])(?=[ ;*])", details)
            class1 = match.group(1)
            if can_remove_section(class1):
                class1 = class1.split("-")[0]
            course.crossclasses.append(class1)

            # Find second cross-listed course code, if any exists
            match = re.search(
                "(?<= and )([A-Z]* [0-9]*-[A-Z0-9][A-Z0-9])(?=[;*])", details)
            if match is not None:
                class2 = match.group(1)
                if can_remove_section(class2):
                    class2 = class2.split("-")[0]
                course.crossclasses.append(class2)

            courses.append(course)
            index += 1

# Remove pseudo-duplicates from list (any entries
# where the course code is shown as a cross-listed
# course in any previous entry)
index = 0
while index < len(courses):
    for code in courses[index].crossclasses:
        position = find_course(courses, code)

        if position != -1:
            del courses[position]

    index += 1

# Write each course to our output file
output = open("cross-listed-courses.txt", "w")
for course in courses:
    output.write(str(course))
    output.write("\n")
output.close()
