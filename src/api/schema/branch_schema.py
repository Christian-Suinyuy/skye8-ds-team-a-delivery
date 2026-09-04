from typing import Literal

from pydantic import BaseModel, Field


class BranchRecord(BaseModel):
    branch_id: str = Field(min_length=1)
    branch_name: Literal[
        "Bamenda Central",
        "Nkwen",
        "Mankon",
        "Bafut",
        "Bali",
        "Kumbo",
        "Jakiri",
        "Ndop",
        "Wum",
        "Fundong",
        "Mbengwi",
        "Batibo",
        "Nkambe",
        "Ndu",
        "Douala Akwa",
        "Douala Bonaberi",
        "Yaounde Mvog-Ada",
        "Yaounde Mokolo",
        "Bafoussam",
        "Dschang",
        "Buea",
        "Limbe",
        "Kribi",
        "Garoua",
    ]
    region: str = Field(min_length=1)
    opened_year: Literal[2009, 2012, 2015, 2017, 2019, 2021, 2023]
    staff_count: Literal[5, 7, 8, 9, 10, 13, 14, 15, 16, 18, 19, 20, 21, 22]
