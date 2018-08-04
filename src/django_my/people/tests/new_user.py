#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import datetime

"""
before exec # vip_date = serializers.DateField(required=False)  people.models.CustomUserSerializer
"""


a_year = datetime.timedelta(days=3650)

for i in range(300, 301):

    data = {
        "email": "3@qq.com",  # "ky" + str(i) +"@ky.com",
        "password": "xinxin123",  # "ky" + str(random.randint(100000, 999999)), datetime.date.today().strftime("%m%d")
        "type": "",
        "vip_date": ""  # str(datetime.date.today() + a_year)
    }
    res = requests.post("http://127.0.0.1:5000/rest/user/", data)
    print json.dumps(json.loads(res.content),
                     indent=4,
                     ensure_ascii=False,
                     )
    f = open("./users.txt", "a")
    # data.pop("vip_date")
    json.dump(data, f, indent=4, ensure_ascii=False
    )
