import requests
import json

from categories import categories
from utility import utility

class ProcessSonar (object):

    def __init__(self, arg):

        self.GROUPID = 'duke-compsci308:'
        if arg is None:
            arg = ""
        self.TEST_PROJECT = self.GROUPID + arg
        self.QUALITY_PROFILE = 'AV-ylMj9F03llpuaxc9n'

        self.SONAR_URL = 'http://coursework.cs.duke.edu:9000'

        self.rulesViolated = []
        self.message = []

        for i in range(5):
            self.rulesViolated.append([])
            self.message.append([])
            k = 0
            if i == 0:
                k = 7
            if i == 1:
                k = 8
            if i == 2:
                k = 5
            for j in range(k):
                self.message[i].append([])


    def process(self, onlyDup):

        #if project not been analysis return error
        r = requests.get(self.SONAR_URL + "/api/components/show?component=" + self.TEST_PROJECT)
        found_project = r.json()
        if 'errors' in found_project:
            return utility().errHandler()

        #get number of pages
        total_pages = utility().getNumOfPages(self.SONAR_URL, self.TEST_PROJECT)

        #get all issues that are open
        issues = utility().getIssues (self.SONAR_URL, self.TEST_PROJECT, total_pages)



        #get all rules associate with quanlity profile
        rules = []
        if not onlyDup:
            r = requests.get(
            self.SONAR_URL + '/api/rules/search?ps=500&activation=true&qprofile=' + self.QUALITY_PROFILE)
            rules.extend(r.json()['rules'])
        else:
            rules.extend(categories().duplications)

        #store details
        dup_errmessages = []
        for issue in issues:
            ruleID = issue['rule']
            ruleResult = filter(lambda r: r['key'] == ruleID, rules)  #rulename = ruleResult[0]['name']

            if len(ruleResult) > 0:
                errmessage = {}
                errmessage['path'] = [issue['component']]
                errmessage['rule'] = ruleResult[0]['name']
                errmessage['message'] = issue['message']
                if ruleID == "common-java:DuplicatedBlocks":

                    dup_errmessages.append(errmessage)
                else:
                    errmessage['textRange'] = []
                    if 'textRange' in issue:
                        errmessage['textRange'].extend(utility().makeTextRange(issue))
                        errmessage['code'] = {}
                        for entry in errmessage['textRange']:
                            locations = entry['locations']
                            for location in locations:
                                startLine = location['textRange']['startLine']
                                endLine = location['textRange']['endLine']
                                r = requests.get(self.SONAR_URL + "/api/sources/show?from=" + str(startLine) +
                                     "&to=" + str(endLine) +
                                     "&key=" + issue['component'])
                                items = r.json()["sources"]

                                errmessage['code'][startLine] = []
                                for item in items:
                                    errmessage['code'][startLine].append(item[1])
                    utility().storeIssue (ruleID, errmessage, self.message, self.rulesViolated)

        #handle duplicated block
        if len(dup_errmessages) > 0:
            utility().duplicatedBlockHandlerStore(self.SONAR_URL, dup_errmessages, self.message, self.rulesViolated)

        #cal percentage
        percentage = []
        percentage.append(utility().calPercentage(categories().communication, self.rulesViolated[0]))
        percentage.append(utility().calPercentage(categories().modularity, self.rulesViolated[1]))
        percentage.append(utility().calPercentage(categories().flexibility, self.rulesViolated[2]))
        percentage.append(utility().calPercentage(categories().javanote, self.rulesViolated[3]))
        percentage.append(utility().calPercentage(categories().codesmell, self.rulesViolated[4]))

        data = utility().dataHandler(self.message, percentage, onlyDup)
        res = json.dumps(data, indent=4, separators=(',', ': '))
        return res

    def statistics(self):

        #http://coursework.cs.duke.edu:9000/api/measures/component?componentKey=duke-compsci308:test&metricKeys=lines
        lines_of_code = "ncloc,"
        lines = "lines,"
        functions = "functions,"
        classes = "classes,"
        files = "files,"
        comment_lines = "comment_lines,"
        comment_lines_density = "comment_lines_density,"

        r = requests.get(
            self.SONAR_URL + '/api/measures/component?componentKey=' +
            self.TEST_PROJECT + "&metricKeys=" + lines_of_code + lines + functions +
            classes + files + comment_lines + comment_lines_density)
        measures = r.json()['component']['measures']
        res = {}
        res ['measures'] = {}
        for measure in measures:
            res['measures'][measure['metric']] = measure['value']

        return json.dumps(res)



    def getrules (self, main, sub):
        #TODO
        res = ""
        return res


if __name__ == '__main__':

    print ProcessSonar("test").process(True)

