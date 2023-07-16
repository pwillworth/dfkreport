#!/usr/bin/env python3
import psycopg2
import dfkInfo

def ReportOptions():
    return {
        'purchaseAddresses': []
    }

def aConn():
    conn = psycopg2.connect("sslmode=verify-full options=--cluster=frugal-toad-1243",
        host = dfkInfo.DB_HOST,
        port = "26257",
	    dbname= dfkInfo.DB_NAME,
	    user = dfkInfo.DB_USER,
	    password = dfkInfo.DB_PASS)
    conn.autocommit = True

    return conn
