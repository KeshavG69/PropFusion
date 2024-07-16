'''Project Outline
We're going to scrape 'https://www.brightmlshomes.com/homes-for-sale/PA'
We'll get a list of cities. For each city , we'll get city name 
For each city, we'll get the houses in the city from the city page
For each house, we'll grab the house address,price,beds,baths,square feet,Lot size,Year Built and house URL
For each topic we'll create a CSV file in the following format:
house address	price	beds	baths	square feet	Lot size	Year Built	House URL
Sunset Lane Abbottstown, PA 17301	$349,900	3	2 Full	1,327	0.57 Acres	2022	https://www.brightmlshomes.com/homes-for-sale/Sunset-Lane-Abbottstown-PA-17301-324786790
and then mail it '''

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
import os
from os.path import basename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import time
from selenium.webdriver.common.keys import Keys
import streamlit as st
from webdriver_manager.chrome import ChromeDriverManager



down=st.number_input("Enter The Down Payment %")
interest=st.number_input("Enter The Rate OF Interest")
length=st.number_input("Enter The Term of Loan")
rance=st.number_input("Enter The Inaurance Money Per Month")
rep=st.number_input("Enter Repair And Mantainence Cost")
reciever_email=st.text_input("Enter Your Email Address")

root='https://www.brightmlshomes.com'

website=f'{root}/homes-for-sale/PA'

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('headless')
chrome_options.add_argument('--disable-dev-shm-usage')


driver = webdriver.Chrome(ChromeDriverManager().install())

driver.get(website)


cities=driver.find_elements(By.TAG_NAME,('td'))


#city ka link
city=cities[0]
cities_data=[]
for city in cities:
  for hrefs in city.find_elements(By.TAG_NAME, ("a")):
    cities_data.append(hrefs.get_attribute('href'))


#link par click karna
#print(driver.current_window_handle)



house_Address=[]
house_Price=[]
house_URL=[]
house_image_url=[]
beds=[]
baths=[]
sqft=[]
pincode=[]
year =[]
typeb=[]
contactname=[]
contactphone=[]
contactcompany=[]
contactadd=[]
tax=[]
walks=[]
bikes=[]
transits=[]
valapp=[]
contact=[]
rent=[]
price=[]
rent2=[]
tax1=[]
loan=[]
rate=[]
irr=[]
ins=[]
cc=[]
man=[]
dpay=[]
term=[]
vac=[]
monpay=[]
totalrev=[]
monrate=[]
totalexpen=[]
montax=[]
monflow=[]
yearflow=[]
tax2=[]
price1=[]
rent3=[]

# df_houses=pd.DataFrame({"Loan Amount":loan,"Interest Rate Per Annum":rate,"Down Payment %":dpay,"Term Of Loan In Years":term,"Mantainence Cost":man,'Address':house_Address, 'Price':price,'URL':house_URL,"Beds":beds,"Baths":baths,"Area":sqft,"Year Of Built":year,"Built Type":typeb,"Bike Score":bikes,"Walk Score":walks,"Transit Score":transits,"Rent Estimate":rent2,"Property Tax Estimate Annual":tax1,"VALUE APPRECIATION%":valapp,"Contact":contact,"AVERAGE IRR":irr,"Closing Cost":cc,"Vacancy":vac,"Monthly Debt Payment":monpay,"Total Monthly Revenue":totalrev,"Total Monthly Expense":totalexpen,"Monthly Tax":montax})

#df_houses.to_csv(f'Properties.csv', mode='a', index=False)


#for i in range(len(cities_data)):
for i in range(14,15):
  driver.execute_script("window.open('');")
  driver.switch_to.window(driver.window_handles[1])
  driver.get(cities_data[i])
 
# #parsing data in the first page

  house_container=WebDriverWait(driver,15).until(EC.presence_of_element_located((By.ID,'listinglanding-main')))
  houses=house_container.find_elements(By.XPATH,("./div[@class='listview-result']"))


  for house in houses:
    house_Address.append(house.find_element(By.TAG_NAME,('a')).text)
    

    house_Price.append(house.find_element(By.TAG_NAME,('span')).text)
    house_url_tag=house.find_element(By.TAG_NAME,('a'))
    house_URL.append(house_url_tag.get_attribute('href'))


  for a in range(len(house_URL)):
    
    driver.execute_script("window.open('');")# Switch to the new window and open URL B
    driver.switch_to.window(driver.window_handles[2+a])
    driver.get(house_URL[a])

    contactname.append(driver.find_element(By.XPATH,("//div/div[@class='lb-agent']")).text)
    contactphone.append(driver.find_element(By.XPATH,("//div/div[@class='lb-phone']")).text)
    contactcompany.append(driver.find_element(By.XPATH,("//div/div[@class='lb-company']")).text)
    contactadd.append(driver.find_element(By.XPATH,("//div/div[@class='lb-address']")).text)
    contact=[contactname[a]+', '+contactphone[a]+' ,'+contactcompany[a]+', '+contactadd[a] ]
    

    try:
      pincode.append(driver.find_element(By.XPATH,("//span[@itemprop='postalCode']")).text)
    except:
      pincode.append('N/A')
    try:
      beds.append(driver.find_element(By.XPATH,("//div[@id='mls-bed2']")).text)
    except:
      beds.append("N/A")
    try:

      baths.append(driver.find_element(By.XPATH,("//div[@id='mls-bath2']")).text)
    except:
      baths.append("N/A")
    try:
      sqft.append(driver.find_element(By.XPATH,("//div[@class='information-block block-square-feet']")).text)
    except:
      sqft.append('N/A')
    try:
      year.append(driver.find_element(By.XPATH,("//div[@id='mls-yr2']")).text)
    except:
      year.append("N/A")
    typeb.append(driver.find_element(By.XPATH,("//div[@id='mls-propt2']")).text)
    try:
      tax.append(driver.find_element(By.XPATH,("//table[@class='tax-history stat-table']/tbody/tr[@class='stat-medium-text']/td[@class='hide-for-vow']")).text)
    except:
      tax.append("N/A")
    try:
      valapp.append(driver.find_element(By.XPATH,("//table[@class='price-history stat-table']/tbody/tr/td[@class='hide-for-vow']/span")).text)
    except:
      valapp.append('0')



    try:
      bikes.append(driver.find_element(By.XPATH,("//div[@id='donut-placeholder-bike']")).text)
    except:
      bikes.append("N/A")
    try:
      walks.append(driver.find_element(By.XPATH,("//div[@id='donut-placeholder-walk']")).text)
    except:
      walks.append('N/A')
    try:
      transits.append(driver.find_element(By.XPATH,("//div[@id='donut-placeholder-transit']")).text)
    except:
      transits.append("N/A")

    rate.append(interest)
    dpay.append(down)
    term.append(length)
    ins.append(rance)
    man.append(length)
    




    

  

  if len(houses)<25:
    pass
    
  elif len(houses)==25:
    next_page=driver.find_element(By.XPATH,("//a[@name='ll-results-next']"))
    next_page.click()
    house_container=WebDriverWait(driver,25).until(EC.presence_of_element_located((By.ID,'listinglanding-main')))
    houses=house_container.find_elements(By.XPATH,("./div[@class='listview-result']"))
    for house in houses:
      house_Address.append(house.find_element(By.TAG_NAME,('a')).text)
      house_Price.append(house.find_element(By.TAG_NAME,('span')).text)
      house_url_tag=house.find_element(By.TAG_NAME,('a'))
      house_URL.append(house_url_tag.get_attribute('href'))
    for a in range(len(house_URL)):
      
      driver.execute_script("window.open('');")# Switch to the new window and open URL B
      driver.switch_to.window(driver.window_handles[2+a])
      driver.get(house_URL[a])

      contactname.append(driver.find_element(By.XPATH,("//div/div[@class='lb-agent']")).text)
      contactphone.append(driver.find_element(By.XPATH,("//div/div[@class='lb-phone']")).text)
      contactcompany.append(driver.find_element(By.XPATH,("//div/div[@class='lb-company']")).text)
      contactadd.append(driver.find_element(By.XPATH,("//div/div[@class='lb-address']")).text)
      contact=contactname[a]+', '+contactphone[a]+' ,'+contactcompany[a]+', '+contactadd[a]    
      try:
        pincode.append(driver.find_element(By.XPATH,("//span[@itemprop='postalCode']")).text)
      except:
        pincode.append('N/A')
      try:
        beds.append(driver.find_element(By.XPATH,("//div[@id='mls-bed2']")).text)
      except:
        beds.append("N/A")
      try:

        baths.append(driver.find_element(By.XPATH,("//div[@id='mls-bath2']")).text)
      except:
        baths.append("N/A")
      try:
        sqft.append(driver.find_element(By.XPATH,("//div[@class='information-block block-square-feet']")).text)
      except:
        sqft.append('N/A')
      try:
        year.append(driver.find_element(By.XPATH,("//div[@id='mls-yr2']")).text)
      except:
        year.append("N/A")
      typeb.append(driver.find_element(By.XPATH,("//div[@id='mls-propt2']")).text)

      
      try:
        valapp.append(driver.find_element(By.XPATH,("//table[@class='price-history stat-table']/tbody/tr/td[@class='hide-for-vow']/span")).text)
      except:
        valapp.append('0')



      try:
        bikes.append(driver.find_element(By.XPATH,("//div[@id='donut-placeholder-bike']")).text)
      except:
        bikes.append("N/A")
      try:
        walks.append(driver.find_element(By.XPATH,("//div[@id='donut-placeholder-walk']")).text)
      except:
        walks.append('N/A')
      try:
        transits.append(driver.find_element(By.XPATH,("//div[@id='donut-placeholder-transit']")).text)
      except:
        transits.append("N/A")

      rate.append(interest)
      dpay.append(down)
      term.append(length)
      ins.append(rance)
      man.append(length)
      




          

  driver.quit()

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('headless')
chrome_options.add_argument('--disable-dev-shm-usage')


driver=webdriver.Chrome(options=chrome_options)
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[0])
driver.get('https://smartasset.com/taxes/pennsylvania-property-tax-calculator#JnfAiNShyT')


locationbox=driver.find_element(By.XPATH,("//td/input[@class='no-autosave ui-autocomplete-input']"))
pricebox=driver.find_element(By.XPATH,("//td/span/input"))
time.sleep(10)

for link in range(0,len(houses)):

  locationbox.clear()
  locationbox.send_keys(pincode[link])
  locationbox.send_keys(Keys.ENTER)
  time.sleep(15)
  pricebox.clear()
  for i in range(0,6):
    pricebox.send_keys(Keys.BACK_SPACE)
  pricebox.send_keys(house_Price[link])
  pricebox.send_keys(Keys.ENTER)
  time.sleep(10)
  tax.append(driver.find_element(By.XPATH,("//td[@class='estimated-tax']/span[@class='value']")).text)
  price1.append(house_Price[link].replace(",",""))
  
  price.append(price1[link].replace("$",""))
  




  # for i in range(len(house_URL)):
  #   tax.remove()
dele=len(house_URL)


del tax[0:dele]



driver.quit()



chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('headless')
chrome_options.add_argument('--disable-dev-shm-usage')


driver=webdriver.Chrome(options=chrome_options)
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[0])


for rent1 in range(0,len(houses)):
  driver.get('https://rental.turbotenant.com/rent-estimate-report')
  searchbox=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,"//div/input[@id='downshift-0-input']")))
  bedbox=driver.find_element(By.XPATH,("//div/input[@id='bedrooms']"))
  typebox=driver.find_element(By.XPATH,("//label/input[@id='all']"))
    
  searchbox.send_keys(house_Address[rent1])
  #(house_Address[link])
  bedbox.send_keys(beds[rent1])
  typebox.click()
  bedbox.send_keys(Keys.ENTER)
  time.sleep(15)
  try:
    rent.append(driver.find_element(By.XPATH,("//div[@class='_3jLbyGzrV-tV18eR_f8xoU']/p[@class='ATivYVhp3Gk5zE9lf9g77']")).text)
  except:
    rent.append("0")
  tax2.append(tax[link].replace(",",""))
  tax1.append(tax2[link].replace("$",""))


for r in range(len(houses)):
  rent3.append(rent[r].replace(",",""))

  rent2.append(rent3[r].replace("$",""))

for i in range(len(price)):
  cc.append(int(price[i])*3/100)
  loan.append(int(price[i])-(int(price[i]))*int(dpay[i])/100)
  vac.append(int(rent2[i])*5/100)

  P=int(price[i])
  R=int(rate[i])/1200

  N=int(term[i])*12
  monpay.append((P*R*(1+R)**N)/((1+R)**(N-1)))
  print(monpay)
  totalrev.append(int(rent2[i])*92/100)
  print(totalrev)
  z=(float(man[i]))
  y=(float(ins[i]))
  x=(float(tax1[i]))/12
  
  totalexpen.append(z+y+x)
  print(totalexpen)
  monflow.append(totalrev[i]-totalexpen[i]-monpay[i])
  print(monflow)
  yearflow.append(monflow[i]*12)
  print(yearflow)
  


chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('headless')
chrome_options.add_argument('--disable-dev-shm-usage')


driver=webdriver.Chrome(options=chrome_options)
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[0])
for calc in range(len(price)):
  driver.get('https://www.calculator.net/rental-property-calculator.html')
  purbox=driver.find_element(By.XPATH,("//input[@id='cprice']"))
  downbox=driver.find_element(By.XPATH,("//input[@id='cdownpayment']"))
  interbox=driver.find_element(By.XPATH,("//input[@id='cinterest']"))
  termbox=driver.find_element(By.XPATH,("//input[@id='cinterest']"))
  ccbox=driver.find_element(By.XPATH,("//input[@id='cothercost']"))
  taxbox=driver.find_element(By.XPATH,("//input[@id='ctax']"))
  insbox=driver.find_element(By.XPATH,("//input[@id='cinsurance']"))
  manbox=driver.find_element(By.XPATH,("//input[@id='cmaintenance']"))
  rentbox=driver.find_element(By.XPATH,("//input[@id='crent']"))
  contbox=driver.find_element(By.XPATH,("//input[@value='Calculate']"))
  but=driver.find_element(By.XPATH,("//label/input[@id='cknowsellprice2']"))
  purbox.clear()
  purbox.send_keys(price[calc])
  downbox.clear()
  downbox.send_keys(dpay[calc])
  interbox.clear()
  interbox.send_keys(rate[calc])
  termbox.clear()
  termbox.send_keys(term[calc])
  ccbox.clear()
  ccbox.send_keys(cc[calc])
  taxbox.clear()
  taxbox.send_keys(tax1[calc])
  insbox.clear()
  insbox.send_keys(ins[calc])
  manbox.clear()
  manbox.send_keys(man[calc])
  rentbox.clear()
  rentbox.send_keys(rent2[calc])
  
  contbox.send_keys(Keys.ENTER)
  irr.append(driver.find_element(By.XPATH,("//td[@class='bigtext']/font/b")).text)

  





















  























df_houses=pd.DataFrame({"Loan Amount":loan,"Interest Rate Per Annum":rate,"Down Payment %":dpay,"Term Of Loan In Years":term,"Mantainence Cost & Repairs":man,"Insaurance":ins,'Address':house_Address, 'Price':house_Price,'URL':house_URL,"Beds":beds,"Baths":baths,"Area":sqft,"Year Of Built":year,"Built Type":typeb,"Bike Score":bikes,"Walk Score":walks,"Transit Score":transits,"Rent Estimate":rent,"Property Tax Estimate Annual":tax,"Contact":contact,"AVERAGE IRR":irr,"Closing Cost":cc,})















df_houses.to_csv(f'Properties.csv', mode='a', index=False, header=True)









def send_email():

  sender_email='gargkeshav1008@gmail.com'
  reciever_email='gargkeshav204@gmail.com,gargkeshav504@gmail.com'

  sender_password = os.environ['gmail_password']
  subject = 'ExcelL File Of All Properties In Pennsylvania'
  content = 'Hey, This is a Excel file of all properties in Pennsylvania'
  msg = MIMEMultipart()
  msg['From'] = sender_email
  msg["To"] =reciever_email
  

  msg['Subject'] = subject
  body = MIMEText(content, 'plain')
  msg.attach(body)  
  filename = 'Properties.csv'
  with open(filename, 'r') as f:
    part = MIMEApplication(f.read(), Name=basename(filename))
    part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(filename))
  msg.attach(part)
  server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
  server_ssl.ehlo()
  server_ssl.login(sender_email,sender_password)
  server_ssl.send_message(msg, from_addr=sender_email, to_addrs=reciever_email.split(','))
    
 




send_email()
   
   

   

print("mail sent")

file = 'Properties.csv'
os.remove(file)
