from docxtpl import DocxTemplate


doc = DocxTemplate("templates/ID_CARD_TEMPLATE_1.docx")
data = {
    "given_name": "ШОХРУХБЕК",
    "surname": "ЙИГИТАЛИЕВ",
    "patronymic": "ТУХТАСИН УГЛИ",
    "date_of_birth": "16.08.2005",
    "citizenship": "УЗБЕКИСТАН",
    "place_of_birth": "ФЕРГАНА",
    "gender": "МУЖСКОЙ",
    "id_number": "AD2590090",
    "date_of_issue": "15.02.2023",
    "date_of_expiry": "15.02.2033",
    "place_of_issue": "ФЕРГАНА УВД 30401",
    "serial_code": "BB76714",
    "personal_number": "51608057040057"
}
doc.render(data)
doc.save("result.docx")