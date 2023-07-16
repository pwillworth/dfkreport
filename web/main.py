#!/usr/bin/env python3
from flask import Flask, request, redirect, url_for
from flask import render_template
from markupsafe import escape
from web3 import Web3
import jsonpickle
import urllib
import db
import utils
import payment
import generate
import view

app = Flask(__name__)

@app.route("/")
def index():
    secondsLeft = -1
    loginState = readAccount(request.args, request.cookies)
    # get subscription status
    if loginState[0] > 0:
        memberStatus = db.getMemberStatus(loginState[1])
        memberState = memberStatus[0]
        secondsLeft = memberStatus[1]
        walletList = memberStatus[3]
    else:
        memberState = 0
        walletList = []
    bankState = 'ragmanEmpty'
    bankMessage = '<span style="color:red;">Warning!</span> <span style="color:white;">Monthly hosting fund goal not reached, please help fill the ragmans crates!</span>'
    balance = balances.readCurrent()
    bankProgress = '${0:.2f}'.format(balance)
    if balance >= 30:
        bankState = 'ragman'
        bankMessage = 'Thank You!  The ragmans crates are full and the hosting bill can be paid this month!'

    return render_template('home.html', memberState=memberState, bankState=bankState, bankProgress=bankProgress, bankMessage=bankMessage)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/help")
def help():
    return render_template('help.html')

@app.route("/generate")
def report_generate():
    # Extract query parameters
    account = request.args.get('account', '')
    wallet = request.args.get('walletAddress', '')
    startDate = request.args.get('startDate', '')
    endDate = request.args.get('endDate', '')
    includeHarmony = request.args.get('includeHarmony', 'on')
    includeDFKChain = request.args.get('includeDFKChain', 'on')
    includeAvalanche = request.args.get('includeAvalanche', 'false')
    includeKlaytn = request.args.get('includeKlaytn', 'on')
    costBasis = request.args.get('costBasis', 'fifo')
    # can be any event group to return only that group of events instead of all
    eventGroup = request.args.get('eventGroup', 'all')
    # Allow for specifying addresses that transfers to should be considered purchases and thus taxable events
    purchaseAddresses = request.args.get('purchaseAddresses', '')

    loginState = readAccount(request.args, request.cookies)

    return generate.generation(account, loginState[0], wallet, startDate, endDate, includeHarmony, includeDFKChain, includeAvalanche, includeKlaytn, costBasis, eventGroup, purchaseAddresses)

@app.route("/view")
def report_view():
    contentFile = request.args.get('contentFile', '')
    # can be set to csv, otherwise json response is returned
    formatType = request.args.get('formatType', '')
    # can be tax or transaction, only used for CSV
    contentType = request.args.get('contentType', '')
    # can be koinlyuniversal or anything else for default
    csvFormat = request.args.get('csvFormat', 'manual')
    # can be any event group to return only that group of events instead of all
    eventGroup = request.args.get('eventGroup', 'all')
    contentFile = db.dbInsertSafe(contentFile)

    return view.getReportData(contentFile, formatType, contentType, csvFormat, eventGroup)

@app.route("/report/<contentid>")
def report_page(contentid=None):
    # escape input to prevent sql injection
    contentFile = db.dbInsertSafe(contentid)

    accounts = ''
    startDate = ''
    endDate = ''
    costBasis = ''
    includedChains = 5
    purchaseAddresses = ''
    bankState = 'ragmanEmpty'
    bankMessage = '<span style="color:red;">Warning!</span> <span style="color:white;">Monthly hosting fund goal not reached, please help fill the ragmans crates!</span>'
    balance = balances.readCurrent()
    bankProgress = '${0:.2f}'.format(balance)
    if balance >= 30:
        bankState = 'ragman'
        bankMessage = 'Thank You!  The ragmans crates are full and the hosting bill can be paid this month!'
    walletGroup = ''
    # When content file is passed, viewing a pregenerated report and we look up its options to preset the form
    if contentid != None and contentFile != '':
        con = db.aConn()
        with con.cursor() as cur:
            cur.execute('SELECT account, startDate, endDate, costBasis, includedChains, moreOptions, walletGroup, wallets FROM reports WHERE reportContent=%s', (contentFile,))
            row = cur.fetchone()
            if row != None:
                account = row[0]
                if row[6] != '':
                    accounts = '{0}'.format(row[6])
                wallets = jsonpickle.decode(row[7])
                for wallet in wallets:
                    accounts = '{0}\n{1}...{2}'.format(accounts, wallet[0:6], wallet[38:42])
                startDate = row[1]
                endDate = row[2]
                costBasis = row[3]
                includedChains = row[4]
                moreOptions = jsonpickle.loads(row[5])
                purchaseAddresses = moreOptions['purchaseAddresses']
                walletGroup = row[6]
        con.close()
    else:
        accounts = 'Error: Report content not found'

    return render_template('report.html', contentFile=contentFile, account=account, startDate=startDate, endDate=endDate, costBasis=costBasis, includedChains=includedChains, purchaseAddresses=purchaseAddresses, walletGroup=walletGroup, wallets=accounts, bankState=bankState, bankProgress=bankProgress, bankMessage=bankMessage))

@app.route("/getReportList")
def report_list():
    loginState = readAccount(request.args, request.cookies)

    if loginState[0] > 0:
        memberState = db.getMemberStatus(loginState[1])[0]
        if memberState == 2:
            listResult = db.getReportList(loginState[1])
        else:
            listResult = 'Error: Subscription not active'
    else:
        listResult = 'Error: Login first to view reports'

    if type(listResult) is not list and (listResult.find("Error:") > -1):
        return { "error" : "'+listResult+'" }
    else:
        reportData = { "reports" : listResult }
        return reportData

@app.route("/getGroupList")
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

@app.route("/postGroupList")
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
            if Web3.isAddress(address):
                addressList.append(Web3.toChecksumAddress(address))
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

@app.route("/removeGroupList")
def del_group_list():
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
        walletList = memberStatus[3]
    else:
        memberState = 0
        walletList = []
    return render_template('member.html', memberState=memberState, memberAccount=loginState[1], secondsLeft=secondsLeft, expiryDescription=utils.timeDescription(secondsLeft), playerWallets=walletList)


@app.route("/addWallet", methods=['POST'])
def add_wallet():
    loginState = readAccount(request.args, request.cookies)
    wallet = request.args.get('wallet','')
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
    wallet = request.args.get('wallet','')
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
