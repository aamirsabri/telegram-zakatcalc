from datetime import datetime
import enum
import logging
from telegram.ext import *
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
import re
from re import sub
from fpdf import FPDF
import os
PORT = int(os.environ.get('PORT', 8443))

TOKEN = "5186791158:AAGqK7ZSlzDch0mp1yfrOlh2-3x0d5QEQuQ"
NOT_VALID_NUMBER = -99
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
proxy = {
    'proxy_url': 'http://10.0.0.6:8080',
}
logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)
GOLD,SILVER,CURRENCY, MERCHANDISE = "Gold" , "Silver" , "Cash in Home - Bank - Commitee - Provident fund", "Row Material - Goods - Plots-House-Flats"
LIABILITY = "Loan - Any Dues - Remaining Bills"
reply_keyboard = [
    [GOLD,SILVER],
    [CURRENCY],
    [MERCHANDISE],
    [LIABILITY],
    ['Done']
]


contries_keyboard = [['UAE'],['India'],['Turkey'],['UAE'],['India'],['Turkey'],['UAE'],['India'],['Turkey'],['UAE'],['India'],['Turkey']]
query = '^(' + GOLD + '|' + SILVER + '|' + CURRENCY + '|' + MERCHANDISE + '|' + LIABILITY +')$'
markup = ReplyKeyboardMarkup(keyboard=reply_keyboard,one_time_keyboard=True)


def start(update:Update,context:CallbackContext) -> int:
    reply_text = "Salam! I will help you to calculate your Zakat.\n Choose the option "
    update.message.reply_text(reply_text,reply_markup=markup)
    
    return CHOOSING

# def build_contries():
#     for contry in contries:
#         button = KeyboardButton(text=contry)


def choice_selection(update:Update,context:CallbackContext) -> int:
    
    choice = update.message.text.lower()
    
    context.user_data['choice'] = choice
    reply_text = ""

    if context.user_data.get(choice):
        reply_text = (f'You already entered {context.user_data.get(choice)} gm of {choice} \nEnter if you want to change')
        if choice is not GOLD and choice is not SILVER :
            reply_text = (f'You already entered {context.user_data.get(choice)} of ({choice}) \nEnter if you want to change')
        
    else:
        reply_text = (f'Please enter How much gm of {choice} do you have ?')
        if choice != GOLD.lower() and choice != SILVER.lower():
            reply_text = (f'Please enter amount for \n ({choice}) \n')
    update.message.reply_text(reply_text)
    return TYPING_REPLY

def calculate_zakat(key,value) -> float:
    totalZakat = 0.0
    if key == GOLD.lower():
        gold_rate = float(get_price("gold"))
        totalZakat = totalZakat + float(int(value) * gold_rate)
    elif key == SILVER.lower():
        silver_rate = float(get_price("silver"))
        totalZakat = totalZakat + float(int(value) * silver_rate)
    elif key == CURRENCY.lower():
        totalZakat = totalZakat + float(value)
    elif key == MERCHANDISE.lower():
        totalZakat = totalZakat + float(value)
    elif key == LIABILITY.lower():
        totalZakat = totalZakat - float(int(value))    
    elif key == 'other':
        totalZakat = totalZakat + float(value)
       
    return totalZakat
       
def calculate_total(user_data:Dict[str,str]) -> str:
    totalZakat = 0.0    
    for key,value in user_data.items():
        totalZakat = totalZakat + calculate_zakat(key,value)
   
    return str(totalZakat)

def create_pdf(user_data:Dict[str,str],username:str,totalZakat:str,currency:str,gold_rate:str,silver_rate:str) -> str:
    pdf = FPDF(orientation='P', unit='mm',format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size = 12)    
    pdf.cell(200,15,txt=f"Zakat Caculation for ({username})\t\t\t\t{datetime.today().strftime('%d-%m-%Y')}",ln=1,align='C')
    totalValue = 0.0
    reply_text =""
    liability = 0.0
    for key,value in user_data.items():
        if is_valid_choice(key):
            if key == LIABILITY.lower():
                liability = float(value)
            if key == GOLD.lower():
                totalValue = totalValue + (float(value) * float(gold_rate))
            elif key == SILVER.lower():
                totalValue = totalValue + (float(value) * float(silver_rate))
            else:
                totalValue = totalValue + float(value)
            pdf.cell(200,6,txt=f"{get_choice_string(key)} - {get_value_string(key,value,currency)}",ln=1)

    pdf.cell(200,20,txt=f"Total Valuation : {totalValue}",ln=1,align='B')    
    pdf.cell(200,5,txt=f"Zakat Payble on : {totalValue - liability}",ln=1)
    pdf.cell(200,10,txt=f"Total Zakat : {totalZakat}",ln=1)
    pdf.cell(200,25,txt="",ln=4,align='B')
    pdf.cell(200,5,txt="Note:",ln=1)
    pdf.cell(200,5,txt=f"Gold Rate : {gold_rate} {currency} per Gram (22K)",ln=1)
    pdf.cell(200,5,txt=f"Silver Rate: {silver_rate} {currency} per Gram",ln=1)
    pdf.cell(200,5,txt="Total Cash : Cash in Home - Bank - Commitee - Provident fund",ln=1)
    pdf.cell(200,5,txt="Total Merchandise : Row Material - Goods - Plots-House-Flats (purchased for selling or reselling purpose",ln=1)
    pdf.cell(200,5,txt="Total Dues : Loan / Any Dues / Remaining Bills / etc",ln=1)
    pdf.cell(200,30,txt="Donate to Dawateislami : https://dawateislamiindia.org",align='C',ln=7)
    pdf.cell(200,5,txt="For any suggession contact on : aamir.kashiri@gmail.com",align='C',ln=1)
    filename = f"{username} zakat_{datetime.today().strftime('%d-%m-%Y')}.pdf"
    pdf.output(filename)
    return filename

def formatted_input(user_data:Dict[str,str]) -> str:
    reply_text = ""
    for key,value in user_data.items():
        if is_valid_choice(key):
            reply_text = f"{reply_text}\n{get_choice_string(key)} - {get_value_string(key,value,'INR')}"
        print(reply_text)
    return reply_text

def is_valid_choice(key:str) -> bool:
    if (key == GOLD.lower() or key == SILVER.lower() or key == CURRENCY.lower() or key == MERCHANDISE.lower() or key == LIABILITY.lower()):
        return True
    return False


def get_choice_string(key:str) -> str:
    if key == GOLD.lower():
        return "Gold"
    elif key == SILVER.lower():
        return "Silver"
    elif key == CURRENCY.lower():
        return "Total Cash"
    elif key == MERCHANDISE.lower():
        return "Total Merchandise"
    elif key == LIABILITY.lower():
        return "All Dues"   
    else:
        return

def get_value_string(key:str,value:str,currency:str) -> str:
    if key == GOLD.lower():
        return f"{value} gm"
    elif key == SILVER.lower():
        return f"{value} gm"
    elif key == LIABILITY.lower():
        return f"(-{value})"
    elif (key == CURRENCY.lower() or key == MERCHANDISE.lower()):
        return f"{value} {currency}"
    else:
        return

def clear_user_data(user_data:Dict[str,str]):
    for key,value in user_data.items():
        user_data[key] = 0
        

def done(update:Update,context:CallbackContext):
    final_result = formatted_input(user_data=context.user_data)
    print(final_result)
    totalZakat = float(calculate_total(context.user_data)) / 40
   
    reply_text = f"Thank you,Hope we will meet again ! \n{final_result} \n\nAs per your input,\n\nTotal zakat is {totalZakat} \n\n Donate to Dawateislami India : \n https://axisbpayments.razorpay.com/pl_IwZjnuiJyfxOXf/view"
    
    update.message.reply_text(reply_text)
    gold_rate = get_price("gold")
    silver_rate = get_price("silver")
    filename = create_pdf(context.user_data,update.message.from_user.full_name,totalZakat=totalZakat,currency='INR',gold_rate=gold_rate,silver_rate=silver_rate)
    zakat_document = open(filename,"rb")
    update.message.reply_document(filename="zakat_calculation.pdf",caption="Your Zakat Calculation",document=zakat_document)
    zakat_document.close()
    
    
    didocument = open("dibooklet.pdf","rb")
    update.message.reply_document(filename="dibooklet.pdf",caption="Dawateislami India Booklet",document=didocument)
    didocument.close()
    
    donationguide = open("donationguide.mp4","rb")
    update.message.reply_video(donationguide,caption="How to Donate")
    donationguide.close()
    # update.message.reply_photo(,caption="Donate Dawateislami from your Zakat, Sadqa ")
    clear_user_data(context.user_data)
    
    return ConversationHandler.END
   
def create_payment_intent():
    payment_intent = stripe.PaymentIntent.create(
        currency= 'inr',
        
    )

def camel_case(s):
  s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
  return ''.join([s[0].lower(), s[1:]])

def result(user_data: Dict[str,str]) -> str:

    final_result = [f'\n {camel_case(key)} : \t\t {value}' for key,value in user_data.items()]
    print(final_result)    
    return "\n".join(final_result).join(['\n','\n'])

def recieve_information(update:Update,context:CallbackContext):
    print(context.user_data)
    data = update.message.text
    if isChoice(data) == True:
        context.user_data['choice'] = update.message.text
        print(f"in recieve  {data}")
        choice_selection(update,context)
        return
    number = get_numeric_value(data)
    if number == NOT_VALID_NUMBER:
        update.message.reply_text("Please  enter valid number,try again!",reply_markup=markup)
        return TYPING_REPLY
    category = context.user_data['choice']
    context.user_data[category] = number
    del context.user_data['choice']
    print(context.user_data)
    reply_text = f"this is what you have already told me \n{formatted_input(context.user_data)} \n\nyou can change your data or press Done when you complete"
    update.message.reply_text(reply_text,reply_markup=markup)    
   
    return CHOOSING

def isChoice(user_input:str) -> bool:
    if user_input == GOLD or user_input == SILVER or user_input == CURRENCY or user_input == MERCHANDISE or user_input == LIABILITY or user_input == 'other':
        return True
    return False
        

def get_numeric_value(text) -> float:
    # numbers = [int(i) for i in text.split() if i.isdigit()]
    numbers = re.findall('[0-9]+', text)
    if len(numbers) == 0:
        return NOT_VALID_NUMBER

    return float(numbers[0])

def get_price(metalType):
    proxies = {
    "http":"http://10.0.0.6:8080",
    "https":"http://10.0.0.6:8080"
    }
    r = requests.get("https://www.goodreturns.in/"+metalType+"-rates/ahmedabad.html")
    c = r.content
    data = BeautifulSoup(c,"html.parser")

    gs_div = data.find_all("div",{"class":"gold_silver_table"})
    gs_rows = gs_div[0].findAll("tr",{"class":"odd_row"})
    gs_cell = gs_rows[0].findAll("td")
    gs_value = gs_cell[1].text
    metal_price = gs_value.replace(",","")
    return metal_price[2:]
   
def main():
    persistance = PicklePersistence(filename='myzakat13')
    updater = Updater(token=TOKEN,persistence=persistance)
    dispatcher = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start',start)],
        states= {
            CHOOSING:[
#                 "Gold" , "Silver" , "Cash in Home - Bank - Commitee - Provident fund", "Row Material - Goods - Plots-House-Flats"
# LIABILITY = "Loan / Any Dues / Remaining Bills"
                
                MessageHandler(Filters.regex('^(' + GOLD + '|' + SILVER + '|' + CURRENCY + '|' + MERCHANDISE + '|' + LIABILITY +')$'),choice_selection)
            ],
            TYPING_REPLY:[
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')),recieve_information)                              
            ]
        },
        fallbacks=[
            MessageHandler(Filters.regex('^Done$'),done)
        ],
        name='zakat_calulation',
        persistent=True,
    )
    dispatcher.add_handler(conv_handler)
#     updater.start_polling()
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url='https://zakatbot-telegram.herokuapp.com/' + TOKEN)        
    
    updater.idle()

if __name__ =="__main__":
    main()
