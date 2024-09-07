from scrapy.signalmanager import dispatcher
from scrapy.crawler import CrawlerProcess
from scrapy import signals
import scrapy
import json
import datetime
import smtplib
from dotenv import load_dotenv
import os

load_dotenv()


def send_dates_by_mail(dates):
    if not dates:
        return

    smtpclient = smtplib.SMTP(host="smtp.gmail.com", port=587)
    smtpclient.starttls()
    smtpclient.login(os.getenv('GMAIL_USERNAME'), os.getenv('GMAIL_PASSWORD'))
    msg = "From: me@localhost\n" \
          "Subject: Dates found\n\n"

    msg += "\n".join(["{} - {}".format(x['profession_name'], x['date']) for x in dates])

    smtpclient.sendmail("me@localhost", [os.getenv('GMAIL_USERNAME')], msg.encode('utf8'))


class ClalitChecker(scrapy.Spider):
    name = "Clalit Checker"
    login_url = "https://e-services.clalit.co.il/OnlineWeb/General/Login.aspx"
    appointments_url = "https://e-services.clalit.co.il/OnlineWeb/Services/Tamuz/TamuzTransfer.aspx"
    appointments_iframe_url = "https://e-services.clalit.co.il/OnlineWeb/Services/Tamuz/TamuzTransferContentByService" \
                              ".aspx?MethodName=TransferWithAuth"
    appointments_iframe_login_url = "https://e-services.clalit.co.il/Zimunet/Visits/Login"
    appointment_url = "https://e-services.clalit.co.il/Zimunet/AvailableVisit/GetMonthlyAvailableVisit?id={}&" \
                      "professionType=Professional&month={}&year={}&isUpdateVisit=True"

    def parse(self, response, **kwargs):
        appointments = [
            (visit.attrib['data-id'],
             datetime.datetime.strptime(visit.css("span.visitDateTime")[0].root.text, "%d.%m.%Y"),
             visit.css("div.professionName")[0].root.text
             )
            for visit in response.css("#futureVisitsSection li.visit") if 'data-id' in visit.attrib
        ]
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year

        return [scrapy.FormRequest(url=self.appointment_url.format(appointment, month, year),
                                   cb_kwargs=dict(
                                       appointment=appointment,
                                       month=month,
                                       year=year,
                                       original_date=original_date,
                                       profession_name=professionName,
                                   ),
                                   callback=self.handle_appointments)
                for appointment, original_date, professionName in appointments]

    def handle_appointments(self, response, appointment, month, year, original_date, profession_name):
        if response.body:
            data = json.loads(response.body)
            if data['errorType'] == 0:
                for d in data['data']['availableDays']:
                    if datetime.datetime.strptime(d, "%d.%m.%Y") < original_date:
                        yield {"date": d, "profession_name": profession_name}

            elif data['errorType'] == 1:
                next_month = month == 12 and 1 or month + 1
                next_year = month == 12 and year + 1 or year
                if datetime.datetime.strptime("{}.{}.{}".format(1, next_month, next_year), "%d.%m.%Y") < original_date:
                    yield scrapy.FormRequest(url=self.appointment_url.format(appointment, next_month, next_year),
                                             cb_kwargs=dict(
                                                 appointment=appointment,
                                                 month=next_month,
                                                 year=next_year,
                                                 original_date=original_date,
                                                 profession_name=profession_name,
                                             ),
                                             callback=self.handle_appointments)

            elif data['errorType'] == 3:
                self.logger.error("There was an error in Clalit's website")

    def start_requests(self):
        return [scrapy.Request(self.login_url, callback=self.handle_login)]

    def handle_login(self, response):
        form_data = {x.attrib['name']: x.attrib['value'] if 'value' in x.attrib else '' for x in response.css('input')}

        form_data['ctl00$cphBody$_loginView$tbUserId'] = os.getenv('CLALIT_USER_ID')
        form_data['ctl00$cphBody$_loginView$tbUserName'] = os.getenv('CLALIT_USER_NAME')
        form_data['ctl00$cphBody$_loginView$tbPassword'] = os.getenv('CLALIT_PASSWORD')
        form_data['__EVENTTARGET'] = "ctl00$cphBody$_loginView$btnSend"

        inputs_to_remove = ['ctl00$cphBody$_loginView$imgHelpUserId', 'ctl00$cphBody$_loginView$imgHelpUserName',
                            'ctl00$cphBody$_loginView$imgHelpPassword', 'ctl00$cphBody$_loginView$imgHelpCaptcha',
                            'ctl00$mdModalDialogNonSecureMatser$MyButtonCtrl']

        for input_to_remove in inputs_to_remove:
            del form_data[input_to_remove]

        return scrapy.FormRequest(url=self.login_url, method="POST", formdata=form_data, callback=self.after_login)

    def after_login(self, response):
        if not response.url.endswith("FamilyHomePage.aspx"):
            raise Exception("login didn't work")

        return scrapy.Request(self.appointments_url, callback=self.handle_iframe)

    def handle_iframe(self, response):
        return scrapy.Request(self.appointments_iframe_url, callback=self.handle_iframe_login)

    def handle_iframe_login(self, response):
        form_data = {x.attrib['name']: x.attrib['value'] if 'value' in x.attrib else '' for x in response.css('input')}
        return scrapy.FormRequest(url=self.appointments_iframe_login_url, method="POST", formdata=form_data)


def main():
    outfile = os.getenv('OUT_FILE')
    settings = {
        'FEEDS':
            {
                outfile: {
                    'overwrite': True,
                    'format': 'json'
                }
            }
    } if outfile else {}
    results = []

    def crawler_results(signal, sender, item, response, spider):
        results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_passed)
    process = CrawlerProcess(settings={
        "USER_AGENT": 'Mozilla/5.0 (Android 10; Mobile; rv:88.0) Gecko/88.0 Firefox/88.0',
        **settings
    })
    process.crawl(ClalitChecker)
    process.start()

    if os.getenv('GMAIL_USERNAME'):
        send_dates_by_mail(results)


if __name__ == "__main__":
    main()
