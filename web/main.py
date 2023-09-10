#!/usr/bin/env python3
from flask import Flask, request, redirect, url_for
from flask import render_template
from flask import make_response
from markupsafe import escape
from web3 import Web3
from datetime import timezone, datetime, date
import logging
from flask.logging import default_handler
import urllib
import db
import utils
import payment
import generate
import view

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
root = logging.getLogger()
root.addHandler(default_handler)

app = Flask('dfkreport')

@app.route("/")
@app.route("/home")
def index():
    secondsLeft = -1
    loginState = readAccount(request.args, request.cookies)
    # get subscription status
    if loginState[0] > 0:
        memberStatus = db.getMemberStatus(loginState[1])
        memberState = memberStatus[0]
        secondsLeft = memberStatus[1]
    else:
        memberState = 0
    bankState = 'ragmanEmpty'
    bankMessage = '<span style="color:red;">Warning!</span> <span style="color:white;">Monthly hosting fund goal not reached, please help fill the ragmans crates!</span>'
    balance = db.readBalance()
    bankProgress = '${0:.2f}'.format(balance)
    if balance >= 30:
        bankState = 'ragman'
        bankMessage = 'Thank You!  The ragmans crates are full and the hosting bill can be paid this month!'

    return render_template('home.html', memberState=memberState, bankState=bankState, bankProgress=bankProgress, bankMessage=bankMessage)

@app.route("/about")
def about():
    return render_template('about.html', BASE_SCRIPT_URL='/')

@app.route("/help")
def help():
    return render_template('help.html', BASE_SCRIPT_URL='/')

@app.route("/generate", methods=['GET','POST'])
def report_generate():
    # Extract query parameters
    account = request.form.get('account', '')
    wallet = request.form.get('walletAddress', '')
    startDate = request.form.get('startDate', '')
    endDate = request.form.get('endDate', '')
    includeHarmony = request.form.get('includeHarmony', 'undefined')
    includeDFKChain = request.form.get('includeDFKChain', 'undefined')
    includeAvalanche = request.form.get('includeAvalanche', 'false')
    includeKlaytn = request.form.get('includeKlaytn', 'undefined')

    loginState = readAccount(request.args, request.cookies)
    # ensure account passed is checksum version when logged in otherwise use wallet
    if loginState[0] > 0:
        account = loginState[1]
    else:
        if account == '':
            account = wallet

    return generate.generation(account, loginState[0], wallet, startDate, endDate, includeHarmony, includeDFKChain, includeAvalanche, includeKlaytn)

@app.route("/pnl/<content_type>", methods=['GET', 'POST'])
def pnl(content_type=None):
    failure = False
    includedChains = 0
    walletGroup = ''
    wallets = []
    # Extract query parameters
    account = request.form.get('account', '')
    wallet = request.form.get('walletAddress', '')
    startDate = request.form.get('startDate', '')
    endDate = request.form.get('endDate', '')
    includeHarmony = request.form.get('includeHarmony', 'undefined')
    includeDFKChain = request.form.get('includeDFKChain', 'undefined')
    includeAvalanche = request.form.get('includeAvalanche', 'false')
    includeKlaytn = request.form.get('includeKlaytn', 'undefined')
    # can be set to csv, otherwise json response is returned
    formatType = request.form.get('formatType', '')
    # can be tax or transaction, only used for CSV
    contentType = request.form.get('contentType', '')

    # can be koinlyuniversal or anything else for default
    csvFormat = request.args.get('csvFormat', '')
    if csvFormat != '':
        formatType = request.args.get('formatType', formatType)
        contentType = request.args.get('contentType', contentType)
        account = request.args.get('account', account)
        wallet = request.args.get('walletAddress', wallet)
        startDate = request.args.get('startDate', startDate)
        endDate = request.args.get('endDate', endDate)
        includeHarmony = request.args.get('includeHarmony', includeHarmony)
        includeDFKChain = request.args.get('includeDFKChain', includeDFKChain)
        includeAvalanche = request.args.get('includeAvalanche', includeAvalanche)
        includeKlaytn = request.args.get('includeKlaytn', includeKlaytn)

    costBasis = request.form.get('costBasis', 'fifo')
    # can be any event group to return only that group of events instead of all
    eventGroup = request.form.get('eventGroup', 'all')
    # Allow for specifying addresses that transfers to should be considered purchases and thus taxable events
    purchaseAddresses = request.form.get('purchaseAddresses', '')
    addressList = []
    otherOptions = db.ReportOptions()
    if purchaseAddresses != '':
        purchaseAddresses = urllib.parse.unquote(purchaseAddresses)
        if ',' in purchaseAddresses:
            input = purchaseAddresses.split(',')
        else:
            input = purchaseAddresses.split()
        for address in input:
            address = address.strip()
            if Web3.is_address(address):
                addressList.append(Web3.to_checksum_address(address))
            elif len(address) == 0:
                continue
            else:
                response = ''.join(('{ "response" : "Error: You have an invalid address in the purchase address list ', address, '." }'))
                failure = True
        otherOptions['purchaseAddresses'] = addressList

    loginState = readAccount(request.args, request.cookies)
    # ensure account passed is checksum version when logged in otherwise use wallet
    if loginState[0] > 0:
        account = loginState[1]
    else:
        if account == '':
            account = wallet

    try:
        tmpStart = datetime.strptime(startDate, '%Y-%m-%d').date()
        tmpEnd = datetime.strptime(endDate, '%Y-%m-%d').date()
    except ValueError:
        response = '{ "response" : "Error: You must provide dates in the format YYYY-MM-DD" }'
        failure = True

    if not Web3.is_address(wallet):
        # If address not passed, check if it is one of users multi wallet groups
        if loginState[0] > 0:
            wallets = db.getWalletGroup(account, wallet)
        if type(wallets) is list and len(wallets) > 0:
            walletGroup = wallet
        else:
            response = { "response" : "Error: {0} is not a valid address.  Make sure you enter the version that starts with 0x".format(wallet) }
            failure = True
    else:
        # Ensure consistent checksum version of address incase they enter lower case
        wallet = Web3.to_checksum_address(wallet)
        wallets = [wallet]

    # Build up the bitwise integer of chains to be included
    if includeHarmony == 'on':
        includedChains += 1
    if includeAvalanche == 'on':
        includedChains += 2
    if includeDFKChain == 'on':
        includedChains += 4
    if includeKlaytn == 'on':
        includedChains += 8
    if includedChains < 1:
        response = { "response" : "Error: You have to select at least 1 blockchain to include." }
        failure = True

    if failure == True:
        result = response
    else:
        if content_type == 'tokens':
            result = view.getTokensReport(wallets, tmpStart, tmpEnd, includedChains)
        elif content_type == 'crafting':
            result = view.getCraftingReport(wallets, tmpStart, tmpEnd, includedChains)
        elif content_type == 'nft':
            result = view.getNFTReport(wallets, tmpStart, tmpEnd, includedChains)
        elif content_type == 'tax':
            result = view.getReportData(formatType, contentType, csvFormat, eventGroup, wallets, tmpStart, tmpEnd, costBasis, includedChains, otherOptions)
        else:
            app.logger.info("Invalid report type passed {0}".format(content_type))
            result = { "error" : "Invalid report type" }

    if formatType == 'csv':
        output = make_response(result)
        output.headers['Content-type'] = 'text/csv'
        output.headers['Content-disposition'] = 'attachment; filename="dfk-report.csv"'
    else:
        output = result

    return output

@app.route("/getReportList", methods=['POST'])
def report_list():
    loginState = readAccount(request.args, request.cookies)

    if loginState[0] > 0:
        memberState = db.getMemberStatus(loginState[1])[0]
        if memberState == 2:
            wallets = db.getWalletGroup(loginState[1])
            listResult = db.getWalletUpdateList(tuple(wallets))
        else:
            listResult = db.getWalletUpdateList(loginState[1])
    else:
        listResult = 'Error: Login first to view reports'

    if type(listResult) is not list and (listResult.find("Error:") > -1):
        return { "error" : "'+listResult+'" }
    else:
        reportData = { "reports" : listResult }
        return reportData

@app.route("/getGroupList", methods=['POST'])
def group_list():
    loginState = readAccount(request.args, request.cookies)
    if loginState[0] > 0:
        listResult = db.getGroupList(loginState[1])
    else:
        listResult = 'Error: Login first to view reports'

    if (listResult.find("Error:") > -1):
        return '{ "error" : "'+listResult+'"}'
    else:
        return '{ "groups" : '+listResult+' }'

@app.route("/postGroupList", methods=['POST'])
def post_group_list():
    loginState = readAccount(request.args, request.cookies)
    groupName = request.args.get("groupName", "")
    wallets = request.args.get("wallets", "")
    # escape input to prevent sql injection
    groupName = db.dbInsertSafe(groupName)

    failure = False
    response = ''
    addressList = []

    if loginState[0] < 1:
        failure = True
        response = ''.join(('{ "error" : "Error: You need be logged in to add or update wallet groups." }'))
    else:
        memberState = db.getMemberStatus(loginState[1])[0]
        if memberState != 2:
            failure = True
            response = ''.join(('{ "error" : "Error: Subscription not active." }'))

    if len(groupName) > 60 or groupName[0:2] == '0x':
        failure = True
        response = ''.join(('{ "error" : "Error: Group Name must be 60 characters or less and cannot begin with 0x." }'))

    if wallets != '' and failure == False:
        walletAddresses = urllib.parse.unquote(wallets)
        if ',' in walletAddresses:
            input = walletAddresses.split(',')
        else:
            input = walletAddresses.split()
        for address in input:
            address = address.strip()
            if Web3.is_address(address):
                addressList.append(Web3.to_checksum_address(address))
            elif len(address) == 0:
                continue
            else:
                response = ''.join(('{ "error" : "Error: You have an invalid address in the wallet list ', address, '." }'))
                failure = True

    print('Content-type: text/json\n')
    if failure == False:
        listResult = db.addGroupList(loginState[1], groupName, addressList)
        response = ''.join(('{ "updated": ', str(listResult), ' }'))

    return response

@app.route("/removeGroupList", methods=['POST'])
def del_group_list():
    failure = False
    loginState = readAccount(request.args, request.cookies)
    groupName = request.args.get("groupName", "")
    # escape input to prevent sql injection
    groupName = db.dbInsertSafe(groupName)

    if loginState[0] < 1:
        failure = True
        response = ''.join(('{ "error" : "Error: You need be logged in to delete wallet groups." }'))

    if failure == False:
        listResult = db.removeGroupList(loginState[1], groupName)
        response = ''.join(('{ "updated": ', str(listResult), ' }'))

    return response

@app.route("/auth")
def auth():
    account = request.args.get("account", "")
    signature = request.args.get("signature", "")
    # escape input to prevent sql injection
    account = db.dbInsertSafe(account)
    signature = db.dbInsertSafe(signature)

    print('Content-type: text/json\n')
    if not Web3.is_address(account):
        sessionResult = 'Error: That is not a valid address.  Make sure you enter the version that starts with 0x'
    else:
        # Ensure consistent checksum version of address
        account = Web3.to_checksum_address(account)
        sessionResult = db.getSession(account, signature)

    return { "sid" : sessionResult }

@app.route("/login")
def login():
    account = request.args.get("account", "")
    sid = request.args.get('sid', '')
    # escape input to prevent sql injection
    account = db.dbInsertSafe(account)
    sid = db.dbInsertSafe(sid)
    # Get a session
    print('Content-type: text/json\n')
    if not Web3.is_address(account):
        nonceResult = 'Error: That is not a valid address.  Make sure you enter the version that starts with 0x'
        return { "error" : str(nonceResult) }
    else:
        # Ensure consistent checksum version of address
        account = Web3.to_checksum_address(account)

        if sid != '':
            sess = db.checkSession(sid)
            if sess == account:
                return { "sid" : sid }
            else:
                nonceResult = db.getAccountNonce(account)
                return { "nonce" : str(nonceResult) }
        else:
            nonceResult = db.getAccountNonce(account)
            return { "nonce" : str(nonceResult) }

@app.route("/logout")
def logout():
    account = request.args.get("account", "")
    sid = request.args.get('sid', '')
    # escape input to prevent sql injection
    account = db.dbInsertSafe(account)
    sid = db.dbInsertSafe(sid)

    loginState = 0

    sess = db.checkSession(sid)
    if (sess != ''):
        loginState = 1
        currentUser = sess

    print('Content-type: text/json\n')
    if not Web3.is_address(account):
        logoutResult = 'Error: That is not a valid address.  Make sure you enter the version that starts with 0x'
    else:
        # Ensure consistent checksum version of address
        account = Web3.to_checksum_address(account)
        if loginState > 0:
            conn = db.aConn()
            cursor = conn.cursor()
            updatestr = 'DELETE FROM sessions WHERE account=%s AND sid=%s'
            cursor.execute(updatestr, (account, sid))
            cursor.close()
            conn.close()
            logoutResult = 'logout complete'
        else:
            logoutResult = 'Error: session was not valid'

    return { "result" : str(logoutResult) }

@app.route("/member")
def member_connect():
    secondsLeft = -1
    loginState = readAccount(request.args, request.cookies)
    # get subscription status
    if loginState[0] > 0:
        memberStatus = db.getMemberStatus(loginState[1])
        memberState = memberStatus[0]
        secondsLeft = memberStatus[1]
    else:
        memberState = 0
    return render_template('member.html', BASE_SCRIPT_URL='/', memberState=memberState, memberAccount=loginState[1], secondsLeft=secondsLeft, expiryDescription=utils.timeDescription(secondsLeft))


@app.route("/addWallet", methods=['POST'])
def add_wallet():
    loginState = readAccount(request.args, request.cookies)
    wallet = request.form.get('wallet','')
    # attempt add if logged in
    if loginState[0] > 0:
        if Web3.is_address(wallet):
            wallet = Web3.to_checksum_address(escape(wallet))
            ud = db.addWallet(loginState[1], wallet)
            if ud > 0:
                result = { "result": ud }
            elif ud == -1:
                result = { "result": ud, "error": "Too many wallets added"}
            else:
                result = { "result": ud, "error": "Wallet is already in list"}
        else:
            result = { "result": 0, "error": "Invalid address" }
    else:
        result = { "result": 0, "error": "Must be logged in" }

    return result

@app.route("/removeWallet", methods=['POST'])
def remove_wallet():
    loginState = readAccount(request.args, request.cookies)
    wallet = request.form.get('wallet','')
    # attempt removal if logged in
    if loginState[0] > 0:
        if Web3.is_address(wallet):
            wallet = Web3.to_checksum_address(escape(wallet))
            ud = db.removeWallet(loginState[1], wallet)
            if ud > 0:
                result = { "result": ud }
            else:
                result = { "result": ud, "error": "Unknown failure" }
        else:
            result = { "result": 0, "error": "Invalid address" }
    else:
        result = { "result": 0, "error": "Must be logged in" }

    return result

@app.route("/validatePayment", methods=['POST'])
def validate_payment():
    result = payment.validatePayment(request.args.get('network', ''), request.args.get('account', ''), request.args.get('txHash', ''))
    return result


@app.errorhandler(404)
def page_not_found(error):
    return render_template('missing.html'), 404

def readAccount(reqArgs, C):
    useCookies = True
    account = ''
    if useCookies:
        try:
            account = C['selectedAccount']
        except KeyError:
            account = reqArgs.get('account', '')
        try:
            sid = C['sid-{0}'.format(account)]
        except KeyError:
            sid = reqArgs.get('sid', '')
    else:
        sid = reqArgs.get('sid', '')
        account = reqArgs.get('account', '')

    sid = db.dbInsertSafe(sid)
    loginState = 0
    if sid != '' and Web3.is_address(account):
        account = Web3.to_checksum_address(account)
        sess = db.checkSession(sid)
        if sess == account:
            loginState = 1
    return [loginState, account]
