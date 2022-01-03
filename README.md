### dfkreport
Defi Kingdoms Transaction History Report Generator

Submission for bounty as outlined here: [Bounty Doc](https://docs.google.com/document/d/1jwoIYrnyJGm31YdLyC3F5yNwUva0EIDrwJqVO9jTnCY/edit)

![Lila](https://dfkreport.cognifact.com/static/images/gettingrecords.gif)
# Lila's Ledger
Lila works hard at Serendale Bank make sure all the people of the kingdoms can get an accurate accounting of thier activity in Defi Kingdoms.
Currently hosted here for review by the community: [Lilas Ledger](https://dfkreport.cognifact.com)

## Components
This Python web application provides a way for anyone to enter thier Harmony Blockchain wallet address and get a report of thier transactions in the game over a date range, as well as a report detailing cost basis accounting of crypto assets sold to show the net gains realized from the value when acquired vs. when sold/traded.

To facilitate this, the server side communicates with the blockchain to get all of the transactions for a wallet address, then parse the details of all of those transactions to interpret the events and produce the financial report.  Once a particular transaction h as been parsed, it is saved in a MariaDB for quicker access if that transaction is ever needed by another request in the future.  The complete results of requested reports are also saved for quick retrieval without the need for parsing if the same report is requested.

## Bounty Parameters
Here outlines the bounty application needs and how they are met by Lila's Ledger:

### Generate a complete transaction history report for any wallet over any customized time frame
The complete history is available on the "Transactions" tab after generation
### Account for every smart contract transaction in the game with a clear line item that is tagged with transaction type and whether this was awarded via a quest, payment, sell of hero, and the price change when sold relative to when received
The relevant received vs. sold price change is found on the "Tax Report" tab after generation
### Quantify all gains and losses for the wallet address entered
The gains and losses are quantified on the "Tax Report" tab, there is also summarized amounts of all transactions on the "Summary" tab for those details that might not be tax relevant.
### Have a mechanism for easily adding all new DFK smart contracts as they are released
The application utilizes a plain datafile containing a dictionary of all DFK smart contracts that can be easily added to.
### Be able to track transactions across multiple EVM based blockchains
The strategy utilized by this submission utlizes blockchain explorer endpoints to retrieve the transaction list for a wallet, then all other interaction is done through a generic web3 sdk which would be agnostic to the EVM chain.  In this setup, addition of each new blockchain to DFK would just require a minimal code update to fetch the transactions for that chain as well to be fed in to the larger program.
### Bonus points for accommodating other currencies than USD 
I kept this in mind during development, and engineered things in such a way as the fiat currency is always parameterized so it would be easier to add in later, but at this time everything is defaulted to USD.  Later enhancement could be done to build out the interface components for currency selection and enhancement of price lookup mechanisms to convert for it, but it is not capable at the time of submission/deadline.

## Usage
Usage help is available on the sites help page [Help](https://dfkreport.cognifact.com/help.py)
