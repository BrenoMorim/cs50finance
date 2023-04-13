# CS50 Finance

My solution for the CS50 finance project of the CS50x course.

| :placard: Vitrine.Dev |     |
| -------------  | --- |
| :sparkles: Nome        | **CS50 Finance**
| :label: Tecnologias | Python, Flask, HTML, Bootstrap, CSS

![Homepage of the project](https://github.com/BrenoMorim/cs50finance/blob/main/project-image.png?raw=true#vitrinedev)

## About the project

> CS50 exercise link: <https://cs50.harvard.edu/x/2023/psets/9/finance/>

The helpers.py file and also some functions of the app.py file were provided by the CS50 staff, so my task as a student was to develop the following features: register, quote, buy, homepage, sell, history and some personal touches as well. I did all the requirements and for the personal touch, I implemented the features of changing passwords, adding cash and also withdrawing money.

## Try it yourself

To run the game yourself, just run the following commands:

```sh
git clone https://github.com/BrenoMorim/cs50finance.git finance
cd finance
virtualenv .venv
source ./.venv/bin/activate
pip install requirements.txt
flask run
```

In order for the project to work properly, you will also need a file called finance.db, which should contain an SQLite database. Furthermore, you must create a .env file containing the variable API_KEY, which is necessary for the IEX cloud service: <https://iexcloud.io/cloud-login#/register/>

---
