import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from flask import current_app
import logging

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
        # Luo verifiointilinkin osoite
        verification_url = f"{current_app.config.get('SITE_URL', 'https://kotiko.io')}/auth/verify?token={verification_token}"
        
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
      <p>&copy; {current_app.config.get('CURRENT_YEAR', '2025')} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')),
            to_emails=To(to_email),
            subject='Tervetuloa Kotiko.io-palveluun - Vahvista sähköpostiosoitteesi',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
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
        # Luo nollauslinkin osoite
        reset_url = f"{current_app.config.get('SITE_URL', 'https://kotiko.io')}/auth/reset-password?token={reset_token}"
        
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
      <p>&copy; {current_app.config.get('CURRENT_YEAR', '2025')} Kotiko.io – Kaikki oikeudet pidätetään.</p>
    </div>
  </div>
</body>
</html>
        """
        
        # Luo viesti
        message = Mail(
            from_email=Email(current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')),
            to_emails=To(to_email),
            subject='Salasanan nollaus - Kotiko.io',
            html_content=HtmlContent(html_content)
        )
        
        # Lähetä viesti käyttäen SendGrid API:a
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
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