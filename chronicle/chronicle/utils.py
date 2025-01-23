from chronicle.parse_parameters import BULK_TEST, ARTICLES, FREQUENCY, OFFSET, SEARCH, LATEST
from bs4 import BeautifulSoup
import json
import re

class CleanData():
    """CLEAN DATA. REMOVES BAD HTML, DUPLICATES, MARKS ADS AND HEADINGS. LOGS DETAILS."""
    def __init__(self, spider, article):
        self.spider = spider
        self.article = article.xpath('./*')
        self.data = {}
        self.run()
    
    def run(self):

        self.find_and_replace_headings()  
        self.remove_bad_html()
        self.remove_duplicates()
        self.find_and_mark_ad_divs()
        self.find_and_replace_align_divs()
        # print(f"Tags after cleaning: {[tag.root.tag for tag in self.article]}")
        self.spider.logger.info(f'DATA CLEANED')

    def find_and_replace_headings(self):
        header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        headers_num = 0

        for tag in self.article:
            if tag.root.tag == 'div' or tag.xpath('string(.)').get().strip() == '':
                continue
            if tag.root.tag in header_tags:
                headers_num += 1
                tag.root.tag = 'h'
                # print(f'Header {tag.root.tag} found and tag replaced with <h>')
                self.spider.logger.info(f'Header {tag.root.tag} found and tag replaced with <h>')
            else:
                content = json.dumps(tag.get())
                if any(f"<{header_tag}" in content for header_tag in header_tags):
                    headers_num += 1
                    tag.root.tag = 'h'
                    # print(f'Nested header found in: {content}. Tag replaced with <h>')
                    self.spider.logger.info(f'Nested header found in: {content}. Tag replaced with <h>')

        self.spider.logger.info(f'{headers_num} headings replaced with <h> tags.')
        return self.article

    def _find_bad_html(self):
        bad_indices = []
        for index, tags in enumerate(self.article):
            if tags.root.tag == 'p':
                visible_text = tags.xpath('string(.)').get().strip()
                normalized_text = re.sub(r'\s+', ' ', visible_text).strip()
                if len(normalized_text) < 49:
                    self.spider.logger.info(f'Bad p tag found: "{normalized_text}" with length {len(normalized_text)}')
                    bad_indices.append(index)
        return bad_indices

    def remove_bad_html(self):
        bad_indices = self._find_bad_html()
        if bad_indices:
            updated_article = [tag for index, tag in enumerate(self.article) if index not in bad_indices]
            # Hope some DOM structure will be preserved
            self.article = updated_article
            self.spider.logger.info(f'Bad html removed')
        return True

    def remove_duplicates(self):
        seen_htmls = set()
        updated_article = []
        duplicate_num = 0
        for tag in self.article:
            html_content = tag.get()
            if html_content not in seen_htmls:
                seen_htmls.add(html_content)
                updated_article.append(tag)
            else:
                duplicate_num += 1
                self.spider.logger.info(f'Duplicate removed')
        
        self.article = updated_article
        self.spider.logger.info(f"{duplicate_num} duplicates removed")
        return self.article

    def find_and_mark_ad_divs(self):
        ad_num = 0
        for tag in self.article:
            if "ADVERTISEMENT" in tag.xpath('string(.)').get():
                ad_num += 1
                tag.root.set("google_ad", "true")
                self.spider.logger.info(f'<div> marked as <ad> tag')
        self.spider.logger.info(f'{ad_num} ads marked with "google_ad" attribute.')
        return self.article

    def find_and_replace_align_divs(self):
        align_num = 0
        for tag in self.article:
            if tag.root.tag == 'div' and ('data-align-right' in tag.attrib or 'data-align-left' in tag.attrib):
                align_num += 1
                tag.root.tag = 'div-aligned'
                # print(f'<div> with align attribute found and replaced with <div-aligned>')
                self.spider.logger.info(f'<div> with align right/left attribute found and replaced with <div-aligned>')
        self.spider.logger.info(f'{align_num} align divs replaced with <div-aligned> tags.')
        return self.article
        
    
class RunTests():
    """TESTS. IMMEDIATELY RAISES IF ANY TEST FAILS. LOGS DETAILS."""

    def __init__(self, spider, article, offset, frequency):
        self.spider = spider
        self.article = article
        self.offset = int(offset)
        self.frequency = int(frequency)
        self.paragraph_tags = ['p']
        self.avoidable_tags = ['h', 'div', 'div-aligned', 'ul', 'ol', 'blockquote']
        self.groups = {}
        self.report = {
            'status': True,
            'details': []
        }
        self.run()

    def run(self):
        try:
            assert self.check_ad_position()
            assert self.divide_tags_into_groups()
            assert self.test_groups()

        except Exception as e:
            self.report['status'] = False
            self.report['details'].append(f'{e}')

    def is_ad(self, tag):
        if tag.root.get("google_ad") == "true":
            return True
        else:
            return False
        
    def check_ad_position(self):
        self.spider.logger.info('Basic ad position check')
        for i, tag in enumerate(self.article):
            if self.is_ad(tag):
                if i == 0:
                    if self.is_ad(self.article[i+1]):
                        raise ValueError(f'Ad found at the beginning of the article')
                elif i == len(self.article) - 1:
                    if self.is_ad(self.article[i-1]):
                        raise ValueError(f'Ad found at the end of the article')
                elif i == len(self.article) - 2:
                    if self.is_ad(self.article[i-1]):
                        raise ValueError(f'Ad found before last tag')
                else:
                    previos_tag = str(self.article[i-1].root.tag)
                    next_tag = str(self.article[i+1].root.tag)
                    if next_tag == 'ad' or previos_tag == 'ad':
                        raise ValueError(f'Ad is next to another ad')
                    if (previos_tag in self.avoidable_tags) or (next_tag in self.avoidable_tags):
                        raise ValueError(f'Ad is between {previos_tag} and {next_tag}')
                    if (previos_tag not in self.paragraph_tags) or (next_tag not in self.paragraph_tags):
                        raise ValueError(f'Ad is next to non-paragraph tag. Paragraph tags are: {self.paragraph_tags}')                                                             
        self.spider.logger.info('Basic ad position test passed')
        return True

    def divide_tags_into_groups(self):
        self.spider.logger.info('Dividing tags into groups')
        try:
            ad_indices = [i for i, tag in enumerate(self.article) if self.is_ad(tag)]
            if not ad_indices:
                raise ValueError('[SOFTERROR] No ads found in article')
            initial_group = [str(tag.root.tag) for tag in self.article[:ad_indices[0]]]
            initial_group.append('ad')

            main_groups = [[str(tag.root.tag) for tag in self.article[ad_indices[i]:ad_indices[i+1]]] for i in range(1, len(ad_indices)-1)]
            for group in main_groups:
                # group.insert(0, 'ad')
                group.append('ad')

            last_group = [str(tag.root.tag) for tag in self.article[ad_indices[-1]:]]
            # last_group.insert(0, 'ad')

            self.groups = {
                "initial_group": initial_group,
                "main_groups": main_groups,
                "last_group": last_group
            }

            self.spider.logger.info(f'Tags divided into groups: {self.groups}')
            return True
        
        except Exception as e:
            raise 
        
    def _test_group(self, group, freq):
        self.spider.logger.info(f'Group: {group}')
        counter = sum(1 for tag in group if tag in self.paragraph_tags)
        if counter < freq:
            raise ValueError(f'Less than {freq} paragraph tags, ad injection is too frequent')
        
        # WHat if e.g. <p> tags number are more than frequency
        count = 0
        aligned_div = False
        for i, tag in enumerate(group):
            self.spider.logger.info(f'Current tag: {tag}, with index: {i}, count: {count}')
            if tag in self.paragraph_tags:
                self.spider.logger.info(f'tag in paragraph tags: {tag}')
                count += 1
            
            if count == freq:
                if group[i-1] == 'div-aligned':
                    self.spider.logger.info(f'ALIGNED DIV FOUND')
                    aligned_div = True

                next_index = i
                while next_index < len(group):
                    next_index += 1
                    next_tag = group[next_index]
                    self.spider.logger.info(f'Next tag: {next_tag}')
                    if next_tag in self.paragraph_tags:

                        if aligned_div:
                            self.spider.logger.info(f'ALIGNED DIV FOUND')
                            # try:
                            if group[next_index+1] == 'ad':
                                self.spider.logger.info('Ad found after 2 paragraphs with aligned div before')
                                raise ValueError(f'[SOFTERROR] Aligned div and two paragraphs found before ad injection')
                            # except IndexError:
                            #     print(f'{}')
                            #     pass

                        raise ValueError(f"Missing ad injection between paragraph tags '{group[next_index-1]}' and '{next_tag}'. Group: {group}. Frequency: {freq}. All tags: {self.groups}")
                    elif next_tag == 'ad': # test success
                        self.spider.logger.info('Ad found')
                        break
                    elif next_tag in self.avoidable_tags:
                        # print(f'Next tag: {next_tag}')
                        if next_tag == 'div-aligned':
                            aligned_div = True
                            self.spider.logger.info(f'Aligned div found')

                        next_index += 1
                        self.spider.logger.info(f'Avoidable tag found: {next_tag}')
                        self.spider.logger.info(f'After avoidable tag: {group[next_index]}')
                        while group[next_index] not in self.paragraph_tags:
                            if group[next_index] == 'ad': 
                                raise ValueError(f'Ad injection after avoidable tag') # this likely won't happen, ad's were already checked for neighbours
                            next_index += 1
                            self.spider.logger.info(f'Looking for p tag after avoidable tag: {group[next_index]}')
                    else:
                        raise ValueError(f'Bad tag found: {next_tag}')
                break
        return True

    def _test_last_group(self):
        group = self.groups.get('last_group')
        self.spider.logger.info(f'Last group: {group}')
        freq = self.frequency
        count = 0
        if 'p' not in self.groups.get('last_group'):
            raise ValueError('At least one paragraph required after last ad')
        for i, tag in enumerate(group):
            if tag in ['p']:
                count += 1
                try:
                    if count >= freq:
                        next_tag = group[i+1]
                        if next_tag in ['p'] and (i+1) != (len(group)-1): # -1 is -'ad' tag
                            raise ValueError('Missing ad injection in last group')
                except IndexError:
                    self.spider.logger.info('IndexError [good]')
                    return True
                except Exception as e:
                    raise ValueError(f'Error: {e}')
        self.spider.logger.info('Last group test passed')
        return True

    def test_groups(self):
        try:
            self.spider.logger.info('Testing first group')
            assert self._test_group(self.groups.get('initial_group'), self.offset)

            self.spider.logger.info('Testing main groups')
            for group in self.groups.get('main_groups'):
                assert self._test_group(group, self.frequency)

            self.spider.logger.info('Testing last group')
            assert self._test_last_group()

            self.spider.logger.info('Groups tests passed')
            return True
        except Exception as e:
            raise

def clean_data_and_run_tests(spider, url, article, bulk_test=BULK_TEST):
    """CLEAN DATA AND RUN TESTS. RETURNS TEST OBJECT."""
    try:
        if SEARCH or LATEST:
            frequency = int(FREQUENCY)
            offset = int(OFFSET)
        else:
            frequency = int(ARTICLES.get(url).get('frequency'))
            offset = int(ARTICLES.get(url).get('offset'))

        spider.logger.info(f"TESTING URL: {url}, offset: {offset}, frequency: {frequency}")
        if not frequency or not offset:
            spider.logger.error(f"Frequency or offset not set for URL: {url}")
            raise SystemError(f"Frequency or offset not set for URL: {url}")

        def _logic(spider=spider, url = url, article=article, frequency=frequency, offset=offset):
            clean_article = CleanData(spider=spider, article=article)
            test = RunTests(spider=spider, article=clean_article.article, frequency=frequency, offset=offset)

            try:
                if '[SOFTERROR]' in test.report.get('details')[0]:
                    test.report['status'] = True
            except Exception:
                pass

            if test.report.get('status'):
                spider.logger.warning(f"ALL TESTS PASSED. URL: {url}, offset: {offset}, frequency: {frequency}, DETAILS: {test.report.get('details')}")
            else:
                spider.logger.error(f"TEST FAILED. URL: {url}, offset: {offset}, frequency: {frequency}. DETAILS: {test.report.get('details')}")
            return test
        
        if bulk_test:
            tests = []
            for freq in range(1, 8):
                for off in range(1, 8):
                    test = _logic(spider=spider, url=url, article=article, frequency=freq, offset=off)
                    tests.append(test)
            return tests
        else:
            return _logic()
    except Exception as e:
        raise