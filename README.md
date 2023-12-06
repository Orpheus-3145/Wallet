# Wallet
Implementation of a desktop app that works as a wallet: it allows to save my expenses and to show them in charts and KPI.


# Structure
## Front-end:
  Thanks to this interface (kivy, python GUI) I can:
  1. write info about my expenses
  2. see the movements I already wrote inside the database
  3. see my current debts/credits
  6. open my BI (see later);

## Back-end:
  The back-end relies on SQL server and pyodbc module to communicate to front-end.

## BI:
  All the data inside the database are representend inside a QlikView sheet, a Business Intelligence tool.
