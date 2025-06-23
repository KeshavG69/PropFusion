import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib

# Mock the entire main.py to prevent actual web scraping and email sending during import
# We'll re-import specific functions as needed for testing.
with patch.dict('sys.modules', {'selenium': MagicMock(), 'smtplib': MagicMock(), 'os': MagicMock(), 'pandas': MagicMock(), 'streamlit': MagicMock(), 'webdrivers_manager': MagicMock()}):
    import main

# Test for the send_email function
@patch('smtplib.SMTP_SSL')
@patch('os.environ.get', return_value='test_password')
@patch('builtins.open', new_callable=MagicMock)
@patch('email.mime.application.MIMEApplication')
def test_send_email_success(mock_mime_application, mock_open, mock_getenv, mock_smtp_ssl):
    """
    Test that send_email function successfully connects, logs in, and sends an email
    with the correct attachments and content.
    """
    # Configure mocks
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_file_handle = mock_open.return_value.__enter__.return_value
    mock_file_handle.read.return_value = b"file_content"
    mock_mime_application.return_value = MagicMock(spec=MIMEApplication)

    # Call the send_email function (mocked main.send_email from initial patch)
    main.send_email()

    # Assertions for SMTP interaction
    mock_smtp_ssl.assert_called_once_with('smtp.gmail.com', 465)
    mock_smtp_instance.ehlo.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with('gargkeshav1008@gmail.com', 'test_password')
    mock_smtp_instance.send_message.assert_called_once()
    mock_smtp_instance.quit.assert_called_once()

    # Assertions for email content and attachment
    # The actual message structure is complex due to MIMEMultipart,
    # so we'll check if the attachment part was created and added.
    mock_mime_application.assert_called_once_with(b"file_content", Name='Properties.csv')
    # The attach method on the MIMEMultipart object (msg) should have been called
    # with the MIMEApplication instance.
    # This is indirectly tested by mocking MIMEApplication and checking its call.
    # A more direct test would inspect the msg object's internal structure if it were returned.

@patch('smtplib.SMTP_SSL', side_effect=smtplib.SMTPAuthenticationError('auth_error', 'Failed'))
@patch('os.environ.get', return_value='test_password')
@patch('builtins.open', new_callable=MagicMock)
def test_send_email_authentication_failure(mock_open, mock_getenv, mock_smtp_ssl):
    """
    Test that send_email function handles authentication failures gracefully.
    """
    # Simple call the function; the patch will raise the exception
    with pytest.raises(smtplib.SMTPAuthenticationError);
        main.send_email()

    mock_smtp_ssl.assert_called_once()
    mock_smtp_ssl.return_value.login.assert_called_once()

@patch('smtplib.SMTP_SSL', side_effect=smtplib.SMTPServerDisconnected('disconnected', 'Server disconnected'))
@patch('os.environ.get', return_value='test_password')
@patch('builtins.open', new_callable=MagicMock)
def test_send_email_server_disconnection(mock_open, mock_getenv, mock_smtp_ssl):
    """
    Test that send_email function handles SMTP server disconnection.
    """
    with pytest.raises(smtplib.SMTPServerDisconnected):
          main.send_email()

    mock_smtp_ssl.assert_called_once()


# Note: Due to the global variables and direct screeaecution flow in main.py,
#   proper unit testing of the web scraping and calculation parts is challenging
)  without significant refactoring of main.py into functions that can be imported
  and tested independently.

  If main.py were structured with functions like:
  - get_city_links(driver)
  - get_house_details(driver, city_url)
  - calculate_financials(price, rate, term, etc.)
  - export_to_csv(dataframe)

  Then we could mock the 'driver' object for web scraping functions
  and provide dummy data for financial calculations.

  For this task's scope, given the current structure,
  we will focus on the most isolated and testable part: the send_email function.
  The print statements in main.py also make it hard to assert on output
  without capturing stdout.

# Example of how to test data processing if it were in a function:
# def calculate_financial_metrics(price, dp_percent, interest_rate, loan_term_years,
#                                 maintenance_cost, insurance_cost, annual_tax_estimate):
#     price = float(price)
#     dp_percent = float(dp_percent)
#     interest_rate = float(interest_rate) # Annual rate
#     loan_term_years = float(loan_term_years)
#     maintenance_cost = float(maintenance_cost)
#     insurance_cost = float(insurance_cost)
#     annual_tax_estimate = float(annual_tax_estimate)

#     cc = price * 0.03 # Placeholder for closing cost calculation
#     loan_amount = price - (price * dp_percent / 100)
#     vac = 0.05 * (price * 0.01) # Placeholder for vacancy
#     P = loan_amount
#     R = interest_rate / 1200 # Monthly interest rate
#     N = loan_term_years * 12

#     if N == 0: # Handle division by zero for N=0 term
#         monpay = 0
#     else:
#         monpay = (P * R * (1 + R)**N) / ((1 + R)**N - 1) if R != 0 else P / N

#     totalrev = (price * 0.92)  # Placeholder for total monthly revenue
#     totalexpen = maintenance_cost + insurance_cost + (annual_tax_estimate / 12)
#     monflow = totalrev - totalexpen - monpay
#     yearflow = monflow * 12
#     return cc, loan_amount, vac, monpay, totalrev, totalexpen, monflow, yearflow

# @pytest.mark.parametrize("price, dp, rate, term, man, ins, tax, expected_monpay", [
#     (100000, 20, 5, 30, 100, 50, 1200, 429.52), # Simple case
#     (0, 0, 0, 0, 0, 0, 0, 0), # Zero values
#     (100000, 0, 0, 1, 0, 0, 0, 8333.33), # Edge case: 0 interest, 1 year
#     (100000, 100, 5, 30, 100, 50, 1200, 0) # Edge case: 100% down payment
# ])
# def test_calculate_financial_metrics(price, dp, rate, term, man, ins, tax, expected_monpay):
#     # We ignore other return values for simplicity in this example
#     cc, loan_amount, vac, monpay, totalrev, totalexpen, monflow, yearflow = \
#         calculate_financial_metrics(price, dp, rate, term, man, ins, tax)
#     assert round(monpay, 2) == expected_monpay