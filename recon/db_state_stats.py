#!/usr/bin/python3

import csv
import sys

import doltcli as dolt

def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("{} <dolt_db_dir>".format(sys.argv[0]))
        return

    db = dolt.Dolt(sys.argv[1])

    out_f = open("db_state_stats.csv", "w")
    csv_writer = csv.DictWriter(out_f, fieldnames=["state_code", "count"])
    csv_writer.writeheader()

    sql = "SELECT `code` FROM `states`;"
    print(sql)
    res = db.sql(sql, result_format="json")

    for row in res["rows"]:
        state_code = row['code']

        sql2 = 'SELECT COUNT(*) FROM `sales` WHERE `state` = "{}";'.format(state_code)
        print(sql2)

        res2 = db.sql(sql2, result_format="json")

        count = res2['rows'][0]['COUNT(*)']

        csv_row = {
            'state_code': state_code,
            'count': count
        }

        print(csv_row)

        csv_writer.writerow(csv_row)

    out_f.close()

if __name__ == "__main__":
    main()

