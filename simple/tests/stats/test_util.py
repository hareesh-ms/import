# Copyright 2023 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gzip
import os
import sqlite3
import unittest

import pandas as pd
from stats.data import Observation
from stats.data import OBSERVATION_FIELD_NAMES
from stats.data import Triple

# If $TEST_MODE is set to "write", the test will write the goldens.
_TEST_MODE = os.getenv("TEST_MODE", "")
_WRITE_MODE = "write"


def is_write_mode() -> bool:
  return _TEST_MODE == _WRITE_MODE


def compare_files(test: unittest.TestCase,
                  actual_path: str,
                  expected_path: str,
                  message: str = None):
  """
  Compares the content of the actual and expected files and asserts their equality.
  """
  # Pass if neither actual nor existing file exists.
  # Fail if only one exists.
  actual_file_exists = os.path.exists(actual_path)
  expected_file_exists = os.path.exists(expected_path)
  test.assertEqual(
      actual_file_exists, expected_file_exists,
      f"Actual file existence does not match expected file existence: {message}"
  )
  if (expected_file_exists == False):
    return

  with open(actual_path) as gotf:
    got = gotf.read()
    with open(expected_path) as wantf:
      want = wantf.read()
      test.assertEqual(got, want, message)


def read_triples_csv(path: str) -> list[Triple]:
  """
  Reads a triples CSV into a list of Triple objects.
  """
  df = pd.read_csv(path, keep_default_na=False)
  return [Triple(**kwargs) for kwargs in df.to_dict(orient='records')]


def write_observations(db_path: str, output_path: str):
  """
  Fetches all observations from a sqlite db at db_path
  and writes it to the output_path CSV.
  """
  with sqlite3.connect(db_path) as db:
    rows = db.execute("select * from observations").fetchall()
    pd.DataFrame(rows, columns=OBSERVATION_FIELD_NAMES).to_csv(output_path,
                                                               index=False)


def write_triples(db_path: str, output_path: str):
  """
  Fetches all triples from a sqlite db at db_path
  and writes it to the output_path CSV.
  """
  with sqlite3.connect(db_path) as db:
    rows = db.execute("select * from triples").fetchall()
    triples = [Triple(*row) for row in rows]
    write_triples_list(triples, output_path)


def write_triples_list(triples: list[Triple], output_path: str):
  """
  Writes the list of triples to the output_path CSV.
  """
  pd.DataFrame(triples).to_csv(output_path, index=False)


def write_key_values(db_path: str, output_path: str):
  """
  Fetches all key values from a sqlite db at db_path
  and writes it to the output_path CSV.
  """
  with sqlite3.connect(db_path) as db:
    rows = db.execute("select * from key_value_store").fetchall()
    pd.DataFrame(rows, columns=["lookup_key", "value"]).to_csv(output_path,
                                                               index=False)


def write_full_db_to_file(db_path: str, output_path: str):
  """
  Writes a file with SQL statements that can be used to reconstruct the full
  database schema and contents.
  """
  with sqlite3.connect(db_path) as db:
    with open(output_path, 'w') as f:
      for line in db.iterdump():
        f.write('%s\n' % line)


def read_full_db_from_file(db_path: str, input_path: str):
  """
  Reconstructs a database's schema and contents from a file with a series of
  SQL commands.
  """
  with sqlite3.connect(db_path) as db:
    with open(input_path, 'r') as f:
      db.cursor().executescript(f.read())


class FakeGzipTime:

  def __init__(self, timestamp=0) -> None:
    self.timestamp = timestamp

  def time(self):
    return self.timestamp


# GZIP encodes a timestamp in the gzipped content which makes test results inconsistent.
# Use this method to make tests use fixed timestamps.
def use_fake_gzip_time(timestamp=0):
  gzip.time = FakeGzipTime(timestamp)
