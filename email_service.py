import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
import logging
import datetime

logger = logging.getLogger(__name__)

def send_verification_email(to_email, verification_token, first_name=None):
    """
    Lähettää sähköpostin varmistuslinkin kanssa.
    
    Args:
        to_email (str): Vastaanottajan sähköpostiosoite
        verification_token (str): Uniikki varmistustoken
        first_name (str, optional): Vastaanottajan etunimi, jos saatavilla
    
    Returns:
        bool: True jos lähetys onnistui, False jos epäonnistui
    """
    try:
        # Hae ympäristömuuttujat
        site_url = os.environ.get('SITE_URL', 'https://kotiko.io')
        current_year = datetime.datetime.now().year
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')
        
        # Luo verifiointilinkin osoite
        verification_url = f"{site_url}/auth/verify?token={verification_token}"
        
        # Käytä etunimi tai oletusarvo
        name_display = first_name if first_name else "käyttäjä"
        
        # HTML-malli sähköpostille (sivuston tyylin mukainen)
        html_content = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tervetuloa Kotiko.io-palveluun</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f8f9fa;
      color: #333;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 30px auto;
      background-color: #ffffff;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      text-align: center;
      padding-bottom: 20px;
      margin-bottom: 25px;
      border-bottom: 1px solid #eee;
    }}
    .header h1 {{
      color: #3498db;
      margin: 0;
      font-size: 28px;
    }}
    .button {{
      display: inline-block;
      margin: 25px 0;
      padding: 12px 24px;
      background-color: #3498db;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: background-color 0.3s;
    }}
    .button:hover {{
      background-color: #2980b9;
    }}
    .footer {{
      font-size: 13px;
      color: #666;
      margin-top: 30px;
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }}
    .info-box {{
      background-color: #f0f0f0;
      padding: 20px;
      border-radius: 8px;
      margin: 25px 0;
      border-left: 4px solid #3498db;
    }}
    .info-box h3 {{
      color: #3498db;
      margin-top: 0;
      font-size: 18px;
    }}
    a {{
      color: #3498db;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .logo {{
      margin-bottom: 15px;
    }}
    p {{
      line-height: 1.6;
      margin: 10px 0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Tervetuloa Kotiko.io-palveluun!</h1>
    </div>

    <p>Hei <strong>{name_display}</strong>,</p>

    <p>Kiitos rekisteröitymisestäsi Kotiko.io-palveluun. Olemme iloisia saadessamme sinut mukaan!</p>

    <p>Vahvista sähköpostiosoitteesi ja viimeistele rekisteröitymisesi klikkaamalla alla olevaa painiketta:</p>

    <div style="text-align: center;">
      <a href="{verification_url}" class="button">Vahvista sähköpostiosoite</a>
    </div>

    <p>Linkki on voimassa 24 tuntia.</p>

    <div class="info-box">
      <h3>Mikä on Kotiko.io?</h3>
      <p>
        Kotiko.io on digitaalinen alusta, jonka avulla voit helposti tutkia, vertailla ja visualisoida asuinrakennuksia – olitpa sitten rakentaja, suunnittelija tai vain kiinnostunut kodin mahdollisuuksista. Palvelumme yhdistää teknologian ja asumisen estetiikan tavalla, joka tekee kodin suunnittelusta entistä inspiroivampaa.
      </p>
    </div>

    <p>Jos et itse rekisteröitynyt palveluumme, voit jättää tämän viestin huomiotta. Tietojasi ei ole tallennettu ilman vahvistustasi.</p>

    <p>Tarvitsetko apua? Ota meihin yhteyttä: <a href="mailto:tuki@kotiko.io">tuki@kotiko.io</a></p>

    <div class="footer">
      <p>&copy; {current_year} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(mail_sender),
            to_emails=To(to_email),
            subject='Tervetuloa Kotiko.io-palveluun - Vahvista sähköpostiosoitteesi',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        api_key = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        # Tarkista vastaus
        if response.status_code in [200, 201, 202]:
            logger.info(f"Verification email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send verification email to {to_email}. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        return False

def send_password_reset_email(to_email, reset_token, first_name=None):
    """
    Lähettää sähköpostin salasanan nollauslinkin kanssa.
    
    Args:
        to_email (str): Vastaanottajan sähköpostiosoite
        reset_token (str): Uniikki nollaustoken
        first_name (str, optional): Vastaanottajan etunimi, jos saatavilla
    
    Returns:
        bool: True jos lähetys onnistui, False jos epäonnistui
    """
    try:
        # Hae ympäristömuuttujat
        site_url = os.environ.get('SITE_URL', 'https://kotiko.io')
        current_year = datetime.datetime.now().year
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')
        
        # Luo nollauslinkin osoite
        reset_url = f"{site_url}/auth/reset-password?token={reset_token}"
        
        # Käytä etunimi tai oletusarvo
        name_display = first_name if first_name else "käyttäjä"
        
        # HTML-malli sähköpostille (sivuston tyylin mukainen)
        html_content = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Salasanan nollaus - Kotiko.io</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f8f9fa;
      color: #333;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 30px auto;
      background-color: #ffffff;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      text-align: center;
      padding-bottom: 20px;
      margin-bottom: 25px;
      border-bottom: 1px solid #eee;
    }}
    .header h1 {{
      color: #3498db;
      margin: 0;
      font-size: 28px;
    }}
    .button {{
      display: inline-block;
      margin: 25px 0;
      padding: 12px 24px;
      background-color: #3498db;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: background-color 0.3s;
    }}
    .button:hover {{
      background-color: #2980b9;
    }}
    .footer {{
      font-size: 13px;
      color: #666;
      margin-top: 30px;
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }}
    a {{
      color: #3498db;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    p {{
      line-height: 1.6;
      margin: 10px 0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Salasanan nollaus</h1>
    </div>

    <p>Hei <strong>{name_display}</strong>,</p>

    <p>Olemme vastaanottaneet pyynnön salasanasi nollauksesta. Voit nollata salasanasi klikkaamalla alla olevaa painiketta:</p>

    <div style="text-align: center;">
      <a href="{reset_url}" class="button">Nollaa salasanani</a>
    </div>

    <p>Tämä linkki on voimassa 24 tuntia. Jos et ole pyytänyt salasanan nollausta, voit jättää tämän viestin huomiotta.</p>

    <p>Tarvitsetko apua? Ota meihin yhteyttä: <a href="mailto:tuki@kotiko.io">tuki@kotiko.io</a></p>

    <div class="footer">
      <p>&copy; {current_year} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(mail_sender),
            to_emails=To(to_email),
            subject='Salasanan nollaus - Kotiko.io',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        api_key = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        # Tarkista vastaus
        if response.status_code in [200, 201, 202]:
            logger.info(f"Password reset email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send password reset email to {to_email}. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False

def send_subscription_renewal_email(to_email, first_name, payment_url):
    """
    Lähettää sähköpostin tilauksen uusimiseksi maksulinkillä.
    
    Args:
        to_email (str): Vastaanottajan sähköpostiosoite
        first_name (str): Vastaanottajan etunimi
        payment_url (str): URL-osoite, josta asiakas voi maksaa tilauksen uusimisen
    
    Returns:
        bool: True jos lähetys onnistui, False jos epäonnistui
    """
    try:
        # Hae ympäristömuuttujat
        current_year = datetime.datetime.now().year
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')
        
        # Käytä etunimi tai oletusarvo
        name_display = first_name if first_name else "käyttäjä"
        
        # HTML-malli sähköpostille (sivuston tyylin mukainen)
        html_content = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tilauksesi uusiminen - Kotiko.io</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f8f9fa;
      color: #333;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 30px auto;
      background-color: #ffffff;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      text-align: center;
      padding-bottom: 20px;
      margin-bottom: 25px;
      border-bottom: 1px solid #eee;
    }}
    .header h1 {{
      color: #3498db;
      margin: 0;
      font-size: 28px;
    }}
    .button {{
      display: inline-block;
      margin: 25px 0;
      padding: 12px 24px;
      background-color: #3498db;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: background-color 0.3s;
    }}
    .button:hover {{
      background-color: #2980b9;
    }}
    .footer {{
      font-size: 13px;
      color: #666;
      margin-top: 30px;
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }}
    .info-box {{
      background-color: #f0f0f0;
      padding: 20px;
      border-radius: 8px;
      margin: 25px 0;
      border-left: 4px solid #3498db;
    }}
    a {{
      color: #3498db;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    p {{
      line-height: 1.6;
      margin: 10px 0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Tilauksesi on uusittava</h1>
    </div>

    <p>Hei <strong>{name_display}</strong>,</p>

    <p>Kuukausitilaksesi Kotiko.io-palvelussa on tulossa päätökseen. Jatkaaksesi palvelun käyttöä ja säilyttääksesi kaikki tietosi ja ominaisuutesi, sinun tulee uusia tilauksesi.</p>

    <div class="info-box">
      <p>Tilauksesi uusiminen varmistaa, että:
        <ul>
          <li>Pääset jatkossakin tekemään analyysejä rajoituksetta</li>
          <li>Kaikki aiemmat tietosi ja analyysisi säilyvät</li>
          <li>Saat käyttöösi kaikki tulevat ominaisuudet ja päivitykset</li>
        </ul>
      </p>
    </div>

    <p>Klikkaa alla olevaa painiketta uusiaksesi tilauksesi helposti ja nopeasti:</p>

    <div style="text-align: center;">
      <a href="{payment_url}" class="button">Uusi tilaukseni</a>
    </div>

    <p>Jos et halua jatkaa tilaustasi, sinun ei tarvitse tehdä mitään. Tilaus päättyy automaattisesti, mutta huomioithan että pääsysi palvelun kaikkiin ominaisuuksiin päättyy.</p>

    <p>Tarvitsetko apua? Ota meihin yhteyttä: <a href="mailto:tuki@kotiko.io">tuki@kotiko.io</a></p>

    <div class="footer">
      <p>&copy; {current_year} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(mail_sender),
            to_emails=To(to_email),
            subject='Uusi tilauksesi Kotiko.io-palvelussa',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        api_key = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        # Tarkista vastaus
        if response.status_code in [200, 201, 202]:
            logger.info(f"Subscription renewal email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send subscription renewal email to {to_email}. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending subscription renewal email: {str(e)}")
        return False

def send_subscription_renewal_reminder_email(to_email, first_name, renewal_date):
    """
    Lähettää muistutussähköpostin lähestyvästä tilauksen uusimisesta.
    
    Args:
        to_email (str): Vastaanottajan sähköpostiosoite
        first_name (str): Vastaanottajan etunimi
        renewal_date (datetime): Päivämäärä, jolloin tilaus uusitaan
    
    Returns:
        bool: True jos lähetys onnistui, False jos epäonnistui
    """
    try:
        # Hae ympäristömuuttujat
        site_url = os.environ.get('SITE_URL', 'https://kotiko.io')
        current_year = datetime.datetime.now().year
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')
        
        # Käytä etunimi tai oletusarvo
        name_display = first_name if first_name else "käyttäjä"
        
        # Formatoi päivämäärä suomalaiseen tyyliin
        formatted_date = renewal_date.strftime("%d.%m.%Y")
        
        # HTML-malli sähköpostille
        html_content = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Muistutus tilauksesi uusimisesta - Kotiko.io</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f8f9fa;
      color: #333;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 30px auto;
      background-color: #ffffff;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      text-align: center;
      padding-bottom: 20px;
      margin-bottom: 25px;
      border-bottom: 1px solid #eee;
    }}
    .header h1 {{
      color: #3498db;
      margin: 0;
      font-size: 28px;
    }}
    .button {{
      display: inline-block;
      margin: 25px 0;
      padding: 12px 24px;
      background-color: #3498db;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: background-color 0.3s;
    }}
    .button:hover {{
      background-color: #2980b9;
    }}
    .footer {{
      font-size: 13px;
      color: #666;
      margin-top: 30px;
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }}
    .info-box {{
      background-color: #f0f0f0;
      padding: 20px;
      border-radius: 8px;
      margin: 25px 0;
      border-left: 4px solid #3498db;
    }}
    a {{
      color: #3498db;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    p {{
      line-height: 1.6;
      margin: 10px 0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Muistutus: Tilauksesi uusitaan pian</h1>
    </div>

    <p>Hei <strong>{name_display}</strong>,</p>

    <p>Tämä on muistutus siitä, että Kotiko.io-palvelun kuukausitilaksesi uusitaan automaattisesti <strong>{formatted_date}</strong>.</p>

    <div class="info-box">
      <p>Kun tilauksesi uusitaan, saat jatkossakin kaikki tilauksesi edut:
        <ul>
          <li>Rajaton pääsy kaikkiin analyysiominaisuuksiin</li>
          <li>Kaikki aiemmat tietosi ja analyysisi säilyvät</li>
          <li>Uusimmat ominaisuudet käytössäsi</li>
        </ul>
      </p>
    </div>

    <p>Voit tarkastella tilaustasi ja laskutustietojasi kirjautumalla tilillesi:</p>

    <div style="text-align: center;">
      <a href="{site_url}/my-subscription" class="button">Tarkastele tilaustasi</a>
    </div>

    <p>Jos et halua jatkaa tilaustasi, voit perua sen tilisi hallintasivulta ennen uusimispäivää.</p>

    <p>Tarvitsetko apua? Ota meihin yhteyttä: <a href="mailto:tuki@kotiko.io">tuki@kotiko.io</a></p>

    <div class="footer">
      <p>&copy; {current_year} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(mail_sender),
            to_emails=To(to_email),
            subject='Muistutus: Kotiko.io-tilauksesi uusitaan pian',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        api_key = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        # Tarkista vastaus
        if response.status_code in [200, 201, 202]:
            logger.info(f"Subscription reminder email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send subscription reminder email to {to_email}. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending subscription reminder email: {str(e)}")
        return False

def send_failed_payment_retry_email(to_email, first_name, payment_url):
    """
    Lähettää sähköpostin epäonnistuneen maksun uusimiseksi.
    
    Args:
        to_email (str): Vastaanottajan sähköpostiosoite
        first_name (str): Vastaanottajan etunimi
        payment_url (str): URL-osoite, josta asiakas voi maksaa tilauksen uusimisen
    
    Returns:
        bool: True jos lähetys onnistui, False jos epäonnistui
    """
    try:
        # Hae ympäristömuuttujat
        current_year = datetime.datetime.now().year
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')
        
        # Käytä etunimi tai oletusarvo
        name_display = first_name if first_name else "käyttäjä"
        
        # HTML-malli sähköpostille
        html_content = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Maksu epäonnistui - Kotiko.io</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f8f9fa;
      color: #333;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 30px auto;
      background-color: #ffffff;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      text-align: center;
      padding-bottom: 20px;
      margin-bottom: 25px;
      border-bottom: 1px solid #eee;
    }}
    .header h1 {{
      color: #e74c3c;
      margin: 0;
      font-size: 28px;
    }}
    .button {{
      display: inline-block;
      margin: 25px 0;
      padding: 12px 24px;
      background-color: #3498db;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: background-color 0.3s;
    }}
    .button:hover {{
      background-color: #2980b9;
    }}
    .footer {{
      font-size: 13px;
      color: #666;
      margin-top: 30px;
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }}
    .info-box {{
      background-color: #fee;
      padding: 20px;
      border-radius: 8px;
      margin: 25px 0;
      border-left: 4px solid #e74c3c;
    }}
    a {{
      color: #3498db;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    p {{
      line-height: 1.6;
      margin: 10px 0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Maksu epäonnistui</h1>
    </div>

    <p>Hei <strong>{name_display}</strong>,</p>

    <p>Valitettavasti kuukausitilaksesi automaattinen uusiminen Kotiko.io-palvelussa epäonnistui. Tämä voi johtua useista syistä, kuten maksukortin vanhenemisesta tai tilapäisestä ongelmasta maksun käsittelyssä.</p>

    <div class="info-box">
      <p><strong>Tärkeää:</strong> Jotta voit jatkaa palvelun käyttöä ilman keskeytyksiä, sinun tulee päivittää maksutietosi ja suorittaa maksu mahdollisimman pian.</p>
    </div>

    <p>Klikkaa alla olevaa painiketta uusiaksesi tilauksesi helposti:</p>

    <div style="text-align: center;">
      <a href="{payment_url}" class="button">Maksa nyt</a>
    </div>

    <p>Jos et halua jatkaa tilaustasi, sinun ei tarvitse tehdä mitään. Huomioithan kuitenkin, että tilauksen päättyessä pääsysi palvelun rajoittamattomiin ominaisuuksiin päättyy.</p>

    <p>Tarvitsetko apua? Ota meihin yhteyttä: <a href="mailto:tuki@kotiko.io">tuki@kotiko.io</a></p>

    <div class="footer">
      <p>&copy; {current_year} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(mail_sender),
            to_emails=To(to_email),
            subject='Tärkeää: Maksusi epäonnistui - Kotiko.io',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        api_key = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        # Tarkista vastaus
        if response.status_code in [200, 201, 202]:
            logger.info(f"Failed payment retry email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send payment retry email to {to_email}. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending payment retry email: {str(e)}")
        return False

def send_subscription_expired_email(to_email, first_name, status):
    """
    Lähettää sähköpostin tilauksen päättyessä.
    
    Args:
        to_email (str): Vastaanottajan sähköpostiosoite
        first_name (str): Vastaanottajan etunimi
        status (str): Tilauksen tila ('cancelled', 'expired', 'payment_failed')
    
    Returns:
        bool: True jos lähetys onnistui, False jos epäonnistui
    """
    try:
        # Hae ympäristömuuttujat
        site_url = os.environ.get('SITE_URL', 'https://kotiko.io')
        current_year = datetime.datetime.now().year
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')
        
        # Käytä etunimi tai oletusarvo
        name_display = first_name if first_name else "käyttäjä"
        
        # Määritä viestin sisältö status-parametrin perusteella
        if status == 'cancelled':
            title = "Tilauksesi on peruutettu"
            message_content = "Olet peruuttanut tilauksesi Kotiko.io-palvelussa. Kiitos ajastasi palvelumme parissa!"
            info_box_content = "Tilauksesi on nyt päättynyt pyyntösi mukaisesti. Pääsysi tilauksen rajoittamattomiin analyyseihin on päättynyt."
        elif status == 'payment_failed':
            title = "Tilauksesi on päättynyt maksun epäonnistumisen vuoksi"
            message_content = "Valitettavasti tilauksesi Kotiko.io-palvelussa on päättynyt, koska tilauksen uusimismaksu epäonnistui useista yrityksistä huolimatta."
            info_box_content = "Voit aktivoida tilauksesi uudelleen milloin tahansa. Kaikki aiemmat analyysisi ovat tallessa ja käytettävissäsi, kun aktivoit tilauksesi uudelleen."
        else:  # expired
            title = "Tilauksesi on päättynyt"
            message_content = "Tilauksesi Kotiko.io-palvelussa on nyt päättynyt. Kiitos ajastasi palvelumme parissa!"
            info_box_content = "Pääsysi tilauksen rajoittamattomiin analyyseihin on päättynyt. Voit aktivoida tilauksesi uudelleen milloin tahansa."
        
        # HTML-malli sähköpostille
        html_content = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} - Kotiko.io</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f8f9fa;
      color: #333;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 30px auto;
      background-color: #ffffff;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      text-align: center;
      padding-bottom: 20px;
      margin-bottom: 25px;
      border-bottom: 1px solid #eee;
    }}
    .header h1 {{
      color: #3498db;
      margin: 0;
      font-size: 28px;
    }}
    .button {{
      display: inline-block;
      margin: 25px 0;
      padding: 12px 24px;
      background-color: #3498db;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: background-color 0.3s;
    }}
    .button:hover {{
      background-color: #2980b9;
    }}
    .footer {{
      font-size: 13px;
      color: #666;
      margin-top: 30px;
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }}
    .info-box {{
      background-color: #f0f0f0;
      padding: 20px;
      border-radius: 8px;
      margin: 25px 0;
      border-left: 4px solid #3498db;
    }}
    a {{
      color: #3498db;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    p {{
      line-height: 1.6;
      margin: 10px 0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{title}</h1>
    </div>

    <p>Hei <strong>{name_display}</strong>,</p>

    <p>{message_content}</p>

    <div class="info-box">
      <p>{info_box_content}</p>
    </div>

    <p>Jos haluat jatkossa uudelleen käyttää palvelua, voit aktivoida uuden tilauksen milloin tahansa:</p>

    <div style="text-align: center;">
      <a href="{site_url}/products" class="button">Katso tilauksemme</a>
    </div>

    <p>Arvostamme palautettasi. Ota meihin yhteyttä: <a href="mailto:tuki@kotiko.io">tuki@kotiko.io</a></p>

    <div class="footer">
      <p>&copy; {current_year} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(mail_sender),
            to_emails=To(to_email),
            subject=f'{title} - Kotiko.io',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        api_key = os.environ.get('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        # Tarkista vastaus
        if response.status_code in [200, 201, 202]:
            logger.info(f"Subscription expiration email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send subscription expiration email to {to_email}. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending subscription expiration email: {str(e)}")
        return False 