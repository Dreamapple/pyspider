#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on __DATE__ by Linghui Meng
# Project: __PROJECT_NAME__
from html2text import html2text
from lxml import html
import re
from urllib.parse import urlparse

from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    crawl_config = {
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('__START_URL__', callback=self.index_page)

    @config(age=7 * 24 * 60 * 60)
    def index_page(self, response):
        # python_console()
        for each in response.doc('a[href^="http"]').items():
            href = each.attr.href
            url = urlparse(href)
            print(url)
            if url.hostname == '__HOST__':
                if re.match(r'^/piadas/[^/]+$', url.path):
                    self.crawl(href, callback=self.index_page)
                elif re.match(r'^/imagens\-engracadas/[^/]+$', url.path):
                    self.crawl(href, callback=self.index_page)

    @config(priority=2)
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }

    def main_page(self, response):
        items = response.etree.xpath('//*[@data-id]')
        for item in items:
            url = item.xpath('.//a')[0].attrib['href']
            link = 'http://www.pikore.com'+url
            self.crawl(link, callback=self.pic_page)
        ul = item.getparent()
        next = 'http://www.pikore.com/user/{a[data-user-id]}/{a[data-next-max-id]}/{a[data-next-page]}'.format(a=ul.attrib)
        save = 'http://www.pikore.com/user/{a[data-user-id]}/'.format(a=ul.attrib)
        self.crawl(next, headers={'x-requested-with':'XMLHttpRequest'},  callback=self.next_page, cookies=response.cookies, save=save)

    def next_page(self, response):
        data = response.text
        # print(data)
        items, z, next_max_id, next_page, x, _ = data.rsplit(';', 5)
        next_max_id = next_max_id.split('.')[-1].split(',')[-1].strip("') ")
        next_page = next_page.split('.')[-1].split(',')[-1].strip("'); ")
        ss = items.split(' = ', 1)[1].replace('$', '', 1)
        items = eval(ss).replace('\/', '/')
        # print(items)
        etree = html.fragments_fromstring(items)
        # print(etree)
        # print('dump:================================================')
        # print(html.tostring(etree))
        for fragment in etree:
            items = fragment.xpath('//*[@data-id]')
            for item in items:
                url = item.xpath('.//a')[0].attrib['href']
                link = 'http://www.pikore.com' + url
                self.crawl(link, callback=self.pic_page)
        next = response.save + next_max_id + '/' + next_page
        self.crawl(next, headers={'x-requested-with': 'XMLHttpRequest'}, callback=self.next_page,
                   cookies=response.cookies, save=response.save)

    @config(priority=2)
    def joke_page(self, response):
        title=response.etree.xpath('//title')
        article_element = response.etree.xpath('')
        if title and article_element:
            article = html.tostring(article_element)

            return {
                "Url": response.url,
                "Title": title,
                "RawHtml":article,
                "Content":html2text(article),
                'Media': 'piadas',
                'Type': 'joke_br',
            }
    @config(priority=2)
    def pic_page(self, response):
        img = response.etree.xpath("/img")
        if not img:
            return
        else:
            img = img[0]
        title = img.attrib['alt'].replace('Instagram media dagelan - ', '')
        imgurl = img.attrib['src']
        save = {
            "Url": response.url,
            "Title": title,
            'Media': '__MEDIA__',
            'Type': '__TYPE__',
        }
        self.crawl(imgurl, callback=self.pic_save, save=save)


    @config(priority=2)
    def pic_save(self, response):
        result = response.save
        result['Binary'] = response.content
        return result