from urlparse import urljoin

import requests
import lxml.html

source_url = 'http://www.parliament.gov.pg/'
resp = requests.get(source_url)
root = lxml.html.fromstring(resp.text)

region_lis = root.xpath("//li[contains(., 'Members')]")[0].find('ul').findall('li')

legislatures_data = [
    {'id': 2012, 'name': '2012-2017', 'start_date': 2012, 'end_date': 2017},
    ]

data = []

for region_li in region_lis:
    region = region_li.find('a').text.strip()
    print "Handling Region: {}".format(region)

    province_lis = region_li.find('ul').findall('li')

    for province_li in province_lis:
        province = province_li.find('a').text.strip()
        print "  - Handling Province: {}".format(province)
        
        district_lis = province_li.find('ul').findall('li')

        for district_li in district_lis:
            member = {
                'term_id': 2012,
                'region': region,
                'province': province,
                }

            district = district_li.find('a').text.strip()
            print "      - Handling District: {}".format(district)
            details_url = urljoin(source_url, district_li.find('a').get('href'))
            
            if district == 'Governor':
                member['area'] = province
                member['executive'] = 'Governor'
            else:
                member['district'] = district
                member['area'] = district

            member_resp = requests.get(details_url)
            member_root = lxml.html.fromstring(member_resp.text)

            member['name'] = member_root.cssselect('.section-head h1')[0].text_content().strip()

            if member['name'] == 'Position is Vacant':
                continue

            member['image'] = urljoin(details_url, member_root.cssselect('.section-body img')[0].get('src'))
            member['party'] = member_root.cssselect('.section-body')[0].xpath("//p[contains(., 'Party')]")[0].find('br').tail.strip()


            parliament_office_p = member_root.xpath("//p[strong[contains(., 'Parliament Office')]]")[0]

            contact_means_list = [x.tail.strip() for x in parliament_office_p.findall('br') if x.tail]

            for contact in contact_means_list:
                try:
                    contact_type, contact_value = contact.split(':')
                    contact_value = contact_value.strip()

                    if contact_type == 'Email':
                        member['email'] = contact_value
                    elif contact_type == 'Telephone':
                        member['phone'] = contact_value
                    elif contact_type == 'Fax':
                        member['fax'] = contact_value
                    else:
                        print "WARNING: Found unknown contact method."
                except ValueError:
                    # Probably there was no colon because it was the snail mail address.
                    pass

            data.append(member)


##########################################################################################
# Actually saving the data is down here to help me add and remove it repeatedly with Git #
##########################################################################################

import scraperwiki
scraperwiki.sqlite.save(unique_keys=['name', 'term_id'], data=data)
scraperwiki.sqlite.save(unique_keys=['id'], data=legislatures_data, table_name='terms')
