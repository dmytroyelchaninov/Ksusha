from chronicle.parse_parameters import VERBOSE

class CleanData():
    def __init__(self, spider, tags, htmls):
        self.spider = spider
        self.tags = tags
        self.htmls = htmls
        self.data = {}
        self.run()
    
    def run(self):
        self.remove_dublicates()
        self.find_and_replace_ad_divs()
        self.find_and_replace_headings()  
        self.remove_bad_html()  
        self.data = {
            'tags': self.tags,
            'htmls': self.htmls
        }
        self.spider.logger.info(f'DATA CLEANED')

    def remove_dublicates(self):
        for index, html in enumerate(self.htmls[1:]):
            if self.htmls[0] == html:
                self.htmls = self.htmls[index + 1:]
                self.tags = self.tags[index + 1:]
                self.spider.logger.info(f"Dublcates removed starting from index {index + 1}")
                return True
        
        self.spider.logger.info('Dublicates not found')
        return False
    
    def find_and_replace_ad_divs(self):
        ad_index = [index for index, value in enumerate(self.htmls) if "ADVERTISEMENT" in value]
        for i in ad_index:
            self.tags[i] = "ad"
        self.spider.logger.info(f'Number of ads replaced: {len(ad_index)}')
        return True
    
    def find_and_replace_headings(self):
        header_tags = ['</h1>', '</h2>', '</h3>', '</h4>', '</h5>', '</h6>']
        indices = [index for index, value in enumerate(self.htmls) if any(tag in value for tag in header_tags)]
        for i in indices:
            self.spider.logger.info(f'Header found: {self.htmls[i]}')
            self.tags[i] = "h"
        self.spider.logger.info(f'Number of headings replaced: {len(indices)}')
        return True
    
    def remove_bad_html(self):
        p_indices = [index for index, tag in enumerate(self.tags) if "p" in tag]
        bad_indices = [index for index in p_indices if len(self.htmls[index]) < 50]
        for i in bad_indices:
            self.tags.pop(i)
            bad_value = self.htmls[i]
            if len(bad_value) < 50:
                self.htmls.pop(i)
                self.spider.logger.info(f'Bad html removed: {bad_value}')
        return True
    

class RunTests():
    """
    TESTS. IMMEDIATELY RAISES IF ANY TEST FAILS. LOGS DETAILS.
    """
    def __init__(self, spider, data):
        self.spider = spider
        self.tags = data.get('tags')
        self.htmls = data.get('htmls')
        self.offset = int(data.get('offset'))
        self.frequency = int((data.get('frequency')))
        self.report = {
            'url': data.get('url'),
            'status': True,
            'details': []
        }
        self.groups = {}
        self.paragraph_tags = ['p']
        self.avoidable_tags = ['h', 'div', 'ul', 'ol', 'blockquote']
        self.run()
    
    def run(self):
        try:
            if VERBOSE:
                self.spider.logger.warning(f'TESTING URL: {self.report.get("url")}, offset: {self.offset}, frequency: {self.frequency}')
            assert self.check_on_neighbours()
            assert self.divide_tags_into_groups()
            assert self.test_groups()
            # assert self.insert_ad()
        except Exception as e:
            self.report['status'] = False
            self.report['details'].append(f'{e}')
            # self.spider.logger.error(f"TEST FAILED. URL: {self.report.get('url')}, DETAILS: {self.report.get('details')}")

    def check_on_neighbours(self):
        self.spider.logger.info('Testing ad neighbours')
        for i, tag in enumerate(self.tags):
            if tag == 'ad':
                if (self.tags[i - 1] not in self.paragraph_tags) or (self.tags[i + 1] not in self.paragraph_tags):
                    raise ValueError(f'Ad has bad neighbours. Ad: {self.htmls[i]}. Surrounded by: {self.htmls[i - 1]} and {self.htmls[i + 1]}')
    
        self.spider.logger.info('Ad neighbours test passed')
        return True

    def divide_tags_into_groups(self):
        try:
            tags = self.tags
            ad_indices = [i for i, val in enumerate(tags) if val == 'ad']
            if not ad_indices:
                return {"initial_group": [], "last_group": [], "sub_groups": set()}

            initial_group = tags[:ad_indices[0] + 1]
            last_group = tags[ad_indices[-1]:]

            sub_groups = set()
            for i in range(len(ad_indices) - 1):
                sub_group = tags[ad_indices[i]:ad_indices[i + 1] + 1]
                sub_groups.add(tuple(sub_group))

            self.groups = {
                "initial_group": initial_group,
                "last_group": last_group,
                "sub_groups": sub_groups
            }

            self.spider.logger.info(f'Tags divided into groups: {self.groups}')
            return True
        
        except Exception as e:
            raise SystemError(f'Error splitting tags into groups: {e}')
        
    # def insert_ad(self):
    #     freq = self.frequency
    #     offset = self.offset
    #     tags = self.tags

    #     tags_clean = [tag for tag in tags if tag != 'ad']
    #     p_counter = 0
    #     offset_inserted = False
    #     insert_indices = []
    #     for i, tag in enumerate(tags_clean):

    #         if p_counter >= offset and not offset_inserted:
    #             if tags_clean[i + 1] in self.paragraph_tags and tags_clean[i] not in self.avoidable_tags:
    #                 insert_indices.append(i+1)
    #                 offset_inserted = True
    #                 p_counter = 0
    #                 continue

    #         if p_counter >= freq:
    #             if tags_clean[i + 1] in self.paragraph_tags and tags_clean[i] not in self.avoidable_tags:
    #                 insert_indices.append(i+1)
    #                 p_counter = 0
    #                 continue

    #         if tag in self.paragraph_tags:
    #             p_counter += 1

    #     for index in insert_indices:
    #         compare = tags_clean.copy()
    #         for index in sorted(insert_indices, reverse=True):
    #             compare.insert(index, 'ad')
        
    #     print(tags)
    #     print(tags_clean)
    #     print(compare)
    #     print(tags)
    #     print(compare == tags)
    #     return compare == tags

    def _test_group(self, group, freq):
        self.spider.logger.info(f'Group: {group}')
        counter = sum(1 for tag in group if tag in self.paragraph_tags)
        # total_tags = sum(1 for tag in group if tag != 'ad')
        if counter < freq:
            raise ValueError(f'Less than {freq} paragraph tags, ad injection is too frequent')
        
        # if counter == freq and total_tags == freq:
        #     return True
        
        # WHat if e.g. <p> tags number are more than frequency
        count = 0
        for i, tag in enumerate(group):
            self.spider.logger.info(f'Current tag: {tag}, with index: {i}, count: {count}')
            if tag in self.paragraph_tags:
                self.spider.logger.info(f'tag in paragraph tags: {tag}')
                count += 1
            
            if count == freq:
                next_index = i
                while next_index < len(group):
                    next_index += 1
                    next_tag = group[next_index]
                    self.spider.logger.info(f'Next tag: {next_tag}')
                    if next_tag in self.paragraph_tags:
                        raise ValueError(f'Missing ad injection between paragraph tags')
                    elif next_tag == 'ad': # test success
                        self.spider.logger.info('Ad found')
                        break
                    elif next_tag in self.avoidable_tags:
                        next_index += 1
                        self.spider.logger.info(f'Avoidable tag found: {next_tag}')
                        self.spider.logger.info(f'After avoidable tag: {group[next_index]}')
                        while group[next_index] not in self.paragraph_tags:
                            if group[next_index] == 'ad': 
                                raise ValueError(f'Ad injection after avoidable tag') # this likely won't happen, 'ad's were already checked for neighbours
                            next_index += 1
                            self.spider.logger.info(f'Looking for p tag after avoidable tag: {group[next_index]}')
                    else:
                        raise ValueError(f'Bad tag found: {next_tag}')
                break
        return True

    def test_groups(self):
        try:
            self.spider.logger.info('Testing first ad')
            assert self._test_group(self.groups.get('initial_group'), self.offset)

            self.spider.logger.info('Testing main groups')
            for group in self.groups.get('sub_groups'):
                assert self._test_group(group, self.frequency)

            self.spider.logger.info('Testing last ad')
            assert self._check_last_ad()

            self.spider.logger.info('Groups tests passed')
            return True

        except Exception as e:
            raise

    def _check_last_ad(self):
        group = self.groups.get('last_group')
        self.spider.logger.info(f'Last group: {group}')
        freq = self.frequency
        count = 0
        if 'p' not in self.groups.get('last_group'):
            raise ValueError('At least one paragraph is required after last ad')
        for i, tag in enumerate(group):
            if tag in ['p']:
                count += 1
                try:
                    if count >= freq:
                        next_tag = group[i+1]
                        if next_tag in ['p'] and (i+1) != (len(group)-1): # -1 is -'ad' tag
                            raise ValueError('Missing AD injection')
                except IndexError:
                    self.spider.logger.info('IndexError [good]')
                    return True
                except Exception as e:
                    raise ValueError(f'Error: {e}')
        return True

    
    