from math import floor, ceil
from datetime import date, datetime
import pandas as pd
import numpy as np
from pandasgui import show
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations


class Leave:
    def __init__(self, date, duration="", sub=[], exclude_hours=set()):
        self.date = date
        self.weekday = date.strftime("%A")
        self.exclude_hours = exclude_hours
        self.duration = duration
        self.leaves = []

    def __repr__(self):
        return str(self.date)


class TimeTable:
    def __init__(self, leaves):
        self.start = datetime(2022, 3, 7)
        self.end = datetime(2022, 6, 13)
        self.file = 'tt2.csv'
        self.sdf = pd.read_csv(self.file, header=0, index_col="Name", dtype=str)
        self.leaves = leaves
        # self.subject_frequency = self.sdf.apply(pd.value_counts).fillna(0)
        # print(self.subject_frequency.to_string())
        # self.subject_frequency["sum"] = self.subject_frequency.sum(axis=1)

        self.p = self.sdf.melt(var_name='Freq', value_name='Subject', ignore_index=False).assign(variable=1) \
            .pivot_table('Freq', 'Name', 'Subject', fill_value=0, aggfunc='count')
        # print(self.p.to_string())
        internals = np.append(pd.date_range(start=datetime(2022, 4, 11), periods=3),
                              pd.date_range(start=datetime(2022, 6, 1), periods=3))
        holidays = pd.date_range(start=datetime(2022, 4, 14), periods=2)
        dates = pd.bdate_range(self.start,
                               self.end,
                               freq='C',
                               holidays=np.append(holidays, internals))
        select_rows = [d.strftime("%A") for d in dates]

        self.s = pd.DataFrame(data={"Total Classes": pd.to_numeric(self.p.loc[select_rows, :].sum())},
                              columns=["Total Classes", "Leaves"]).fillna(0)

        self.s = pd.concat([self.s, self.p.transpose()], axis=1)
        self.subject_frequency = self.sdf.apply(pd.value_counts).fillna(0)
        # print(self.subject_frequency.to_string())

        self.s.iloc[:, 6:14].drop("Mentoring").to_string()

        self.s["Leaves"] = self.calculate_leaves(table=self.s, leaves=self.leaves)
        # print(self.s.to_string())
        self.s["Percentage"] = self.s.apply(self.calc, axis=1)
        self.s["Drop"] = 100 - self.s["Percentage"]
        self.s["Bunkable"] = self.s.apply(self.calculate_bunkable, axis=1)
        for weekday in self.sdf.index:
            self.s[weekday + " 2"] = self.s.apply(self.calc, args=(weekday,), axis=1)

        print(self.s.to_string())

    def calculate_bunkable(self, row):
        return floor((row["Total Classes"] - row["Leaves"]) * 0.25)

    def calculate_leaves(self, table, leaves=[]):
        leaves.extend(self.leaves)
        subjects = Counter()
        hours = self.sdf.columns
        for l in leaves:
            morning_hour = 3 if l.weekday != "Friday" else 4
            if l.duration == "Full":
                h = set(hours)
            if l.duration == "Afternoon":
                h = set(hours[morning_hour:])
            elif l.duration == "Morning":
                h = set(hours[:morning_hour])
            subjects.update(self.sdf.loc[l.weekday, h - l.exclude_hours])
        return table["Leaves"] + pd.Series(subjects, index=table.index, dtype=int).fillna(0)

    def any_k_days(self, k):
        dates = pd.date_range(start=datetime(2022, 3, 14), periods=5)
        s = pd.DataFrame(index=self.s.index, dtype=float)
        for k_dates in tuple(combinations(dates, k)):
            cpy = self.s.copy()
            cpy["Leaves"] = self.calculate_leaves(table=cpy, leaves=[Leave(x, "Afternoon") for x in k_dates])
            cpy["Percentage"] = cpy.apply(self.calc, axis=1)
            s.add(pd.Series(data=cpy.apply(self.calc, axis=1) - 100), axis='index')
        print(s)
        print(s.sum())

    def calc(self, row, weekday=None):
        if weekday:
            return (100 * (row["Total Classes"] - row[weekday] - row["Leaves"]) / row["Total Classes"])
        else:
            return (100 * (row["Total Classes"] - row["Leaves"]) / row["Total Classes"])

    def next_bunkable_day(self):
        q = self.s[(weekday + " 2" for weekday in self.sdf.index)]
        q = (600 - q.sum()).sort_values()
        return q

    def __str__(self):
        return self.s.to_string()

    def get_sub(self):
        return self.s


sradha = [Leave(datetime(2022, 3, 7), "Afternoon", exclude_hours={"4"}),
          Leave(datetime(2022, 3, 8), "Full", exclude_hours={"4", "1", "3"}),
          Leave(datetime(2022, 3, 9), "Full", exclude_hours={"4"}),
          Leave(datetime(2022, 3, 10), "Afternoon", exclude_hours={"4"}),
          Leave(datetime(2022, 3, 11), "Full", exclude_hours={"4", "1", "3"}),
          ]

grace = [Leave(datetime(2022, 3, 8), "Afternoon", exclude_hours={"4"}),
         Leave(datetime(2022, 3, 10), "Full", exclude_hours={"4", "3"}),
         Leave(datetime(2022, 3, 14), "Afternoon", exclude_hours={"4"}),
         Leave(datetime(2022, 3, 24), "Afternoon", exclude_hours={"4"}),
         #Leave(datetime(2022, 3, 18), "Full", exclude_hours={"4"})]
         ]



tt = print(TimeTable(leaves=grace).get_sub().to_string())
# tt.any_k_days(3)
# rint(tt.next_bunkable_day())
# tt.get_sub().to_csv("attendance.csv")
# show(tt.get_sub())
