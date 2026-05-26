# for i in (EOFError, FileExistsError, FileNotFoundError):
# try:
# raise i
# 1 / 0
#
# except Exception as e:
# print(e)
# print(type(e).__doc__)
# print(str(e.__class__).split("'")[1])
# print()


try:
    # raise i
    # 1 / 0
    open("sfomsdf")
except Exception as e:
    print(e)
    print(type(e).__doc__)
    print(str(e.__class__).split("'")[1])
    print()
