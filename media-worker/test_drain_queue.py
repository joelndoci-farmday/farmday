import unittest
from drain_queue import drain
class DrainTests(unittest.TestCase):
 def test_drains_multiple_batches(self):
  values=iter([{"claimed":5},{"claimed":5},{"claimed":0}]); calls=[]
  drain(run=lambda:(calls.append(1) or next(values)),clock=lambda:0,sleep=lambda _:None,budget=20)
  self.assertEqual(len(calls),3)
 def test_empty_queue_exits(self):
  calls=[]
  drain(run=lambda:(calls.append(1) or {"claimed":0}),clock=lambda:0,sleep=lambda _:None,budget=20)
  self.assertEqual(len(calls),2)
if __name__=="__main__":unittest.main()
