"""
DDL generation script.

Simple client for a remote service that produces DDL statements from textual
requirements and logical schema. Intended for tooling and integration testing.
"""

import requests

url = "https://schema2ddl.strangeloop.fun/generate/ddl"
data = {
  "database_requirment": "A university needs a student course selection management system to maintain and track students' course selection information. Students have\ninformation such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or\nchange courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The\npopularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support\nfor academic decision-making",
  "schema": "(1) Student\n- Attribute: student ID, name, age\n- Primary Key: student ID\n\n(2) Course\n- Attribute: course number, course name, credits, lecturer, class time\n- Primary Key: course number\n\n(3) StudentCourses\n- Attribute: student ID, course number\n- Primary Key: student ID, course number\n- Foreign Key: student ID (reference Student: student ID), course number (reference Course: course number)\n    ",
  "target_db_type": "mysql",
  "model": "gpt4"
}
response = requests.post(url, json=data)
print(response.json())
