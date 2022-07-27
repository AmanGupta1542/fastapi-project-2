import ftplib

def ftp_connection(data):
    try:
        ftp_server = ftplib.FTP(data.host, data.user, data.password)
        print(ftp_server)
        ftp_server.encoding = "utf-8"
        return True, ftp_server
    except Exception as e:
        print(e)
        return False, e