from lxml import etree
import random
import sys

from datetime import datetime, date, time, timedelta
import pprint


class Es(object):
    match_start = None

    cmnt = []

    def __init__(self, match_start):
        d = date.today()
        tparts = map(int, match_start.split(':'))
        t = time(tparts[0], tparts[1])
        self.match_start = datetime.combine(d, t)

    def generate_comment(self, written, label, event_type, period, score=0):
        # Compare written and match_start
        c = (written - self.match_start).total_seconds()
        m, s = divmod(c, 60)
        minutes = str(int(m))
        seconds = str(int(s))
        if len(seconds) == 1:
            seconds = "0" + seconds

        time_period = "%s:%s" % (minutes, seconds)

        # End match
        if label == "time" and event_type == "end" and period == "ERT":
            time_period = ""

        self.cmnt.append({
            'written': written.strftime("%Y-%m-%d %H:%M:%S"),
            'label': label,
            'type': event_type,
            'period': period,
            'time': time_period,
            'score': score
        })

    def get_comments(self):
        return self.cmnt

    def run(self, data):

        foo = {
            '1PER': 120,
            '2PER': 120,
            '3PER': 120
        }
        for period, items in data.iteritems():
            const = 0;

            if period == "1PER":
                const = foo['1PER'];
            elif period == "2PER":
                const = foo['1PER'] + foo['2PER']
            elif period == "3PER":
                const = foo['1PER'] + foo['2PER'] + foo['3PER']

            mt = self.match_start

            # Start Period
            if period == "1PER":
                period_start = mt + timedelta(seconds=1)
                if period_start < datetime.now():
                    self.generate_comment(period_start, 'time', 'begin', period)
            elif period == "2PER":
                period_start = mt + timedelta(seconds=20 * 60 + 1)
                if period_start < datetime.now():
                    self.generate_comment(period_start, 'time', 'begin', period)
            elif period == "3PER":
                period_start = mt + timedelta(seconds=40 * 60 + 1)
                if period_start < datetime.now():
                    self.generate_comment(period_start, 'time', 'begin', period)

            for item in items:
                t = map(int, item['time'].split(':'))
                secs = t[0] * 60 + t[1]
                written = self.match_start + timedelta(seconds=secs)
                if written < datetime.now():
                    self.generate_comment(written, 'goal', "", period, item['score'])

            # End Period
            if period == "1PER":
                period_stop = mt + timedelta(seconds=20 * 60)
                if period_stop < datetime.now():
                    self.generate_comment(period_stop, 'time', 'end', '1INT')
            elif period == "2PER":
                period_stop = mt + timedelta(seconds=40 * 60)
                if period_stop < datetime.now():
                    self.generate_comment(period_stop, 'time', 'end', '2INT')
            elif period == "3PER":
                period_stop = mt + timedelta(seconds=60 * 60)
                if period_stop < datetime.now():
                    self.generate_comment(period_stop, 'time', 'end', 'ERT')




class EsXml(Es):
    xml = None
    comments = None

    event_id = None

    score1 = 0
    score2 = 0

    def __init__(self, match_start, event_id):
        Es.__init__(self, match_start)

        self.xml = etree.Element('export', event_id=str(event_id), lang='cs',
                                 last_change=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        scoreboard_element = etree.Element('scoreboard')
        status = self.status()
        scoreboard_element.append(
            etree.Element('status', type=status[0], period=status[1])
        )

        self.xml.append(scoreboard_element)

        self.comments = etree.SubElement(self.xml, 'comments')

        self.event_id = event_id

    def status(self):
        for comment in self.get_comments():
            if comment['label'] == 'time' and comment['type'] == 'end' and comment['period'] == 'ERT':
                return 'finished', 'ERT'

        return 'live', ''

    def make_xml(self, data):
        self.run(data)

        comment_id = self.event_id + 10000

        order = 100000

        comment_list = []

        for comment in self.get_comments():

            comment_id -= 1
            order += 100
            kwargs = {'id': str(comment_id), "order": str(order), 'last_change': comment['written']}
            for k, v in comment.iteritems():
                if k in ('label', 'type', 'written'):
                    kwargs[k] = v

            if "score" in comment and comment['score']:
                if comment['score'] == '1':
                    self.score1 += 1
                if comment['score'] == '2':
                    self.score2 += 1

            kwargs['score1'] = str(self.score1)
            kwargs['score2'] = str(self.score2)

            xml_comment = etree.Element('comment', **kwargs)

            time_element = etree.Element('time', period=comment['period'])
            time_element.text = comment['time']

            details_element = etree.Element('details')

            xml_comment.append(time_element)

            if comment['label'] == 'goal':
                detail_element = etree.Element('detail', id=str(random.randint(1271235, 1971235)))
                detail_element.append(
                    etree.Element('opponent', id="169", global_id="168", code="ZLN")
                )
                for i in range(1, 4):
                    detail_element.append(
                        etree.Element("player%s" % i, name="FooBar")
                    )

                details_element.append(detail_element)

            xml_comment.append(details_element)

            comment_list.append(xml_comment)

        for xml_comment in reversed(comment_list):
            self.comments.append(
                xml_comment
            )

        return etree.tostring(self.xml)


def main(start_time, event_id):

    match = {
        '1PER': [
            {'time': "3:12", "label": "goal", "score": "1"},
            {'time': "8:00", "label": "goal", "score": "1"},
            {'time': "10:12", "label": "goal", "score": "1"},
            {'time': "12:15", "label": "goal", "score": "2"},
        ],
        '2PER': [
            {'time': "22:12", "label": "goal", "score": "1"},
            {'time': "25:15", "label": "goal", "score": "2"},
            {'time': "36:40", "label": "goal", "score": "2"},
        ],
        '3PER': [
            {'time': "50:12", "label": "goal", "score": "1"},
            {'time': "59:15", "label": "goal", "score": "2"},
        ]
    }

    es = EsXml(start_time, event_id)
    output = '<?xml version="1.0" encoding="UTF-8"?>' + es.make_xml(match)

    print output

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Invalid num args'
    else:
        if not ":" in sys.argv[1]:
            print "Invalid time"
        else:
            main(sys.argv[1], int(sys.argv[2]))
