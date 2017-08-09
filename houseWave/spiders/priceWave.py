#coding:utf8

import scrapy
from houseWave.items import HousewaveItem
from scrapy_splash import SplashRequest

import re
import sys

reload(sys)
sys.setdefaultencoding('utf8')


class ScrapeGovhousePriceSpider(scrapy.Spider):
    name = "priceWave"
    #减慢爬取速度，防止被ban
    download_delay = 2
    start_urls = [
        #尝试了 必须是page=1
        'http://www.stats.gov.cn/was5/web/search?page=1&channelid=288041&was_custom_expr=like%28%E4%BD%8F%E5%AE%85%E9%94%80%E5%94%AE%E4%BB%B7%E6%A0%BC%E6%8C%87%E6%95%B0%29%2Fsen&perpage=10&outlinepage=10',
    ]
    #log the info
    # scrapy.log.start(logfile="./log", loglevel=None, logstdout=False)

    def start_requests(self):
        for url in self.start_urls:
            # yield SplashRequest(url, self.parse, args={'wait':1}) #ok
            yield scrapy.Request(url, meta={
                    'splash': {
                        'args': {
                        # set rendering arguments here
                            'html': 1,
                            'png': 1,
                            'wait':1,
                        },
                       
                    }
            })


    #2017年4月份70个大中城市住宅销售价格变动情况
    # print u"=========入库====="
    def parse(self, response):

        print u"执行的url",response.url
        lists  = response.xpath('//li')
        # print response.body
        urlLists = []
        for quote in lists:
            #首先找到住宅销售价格变动的所有月份的网页
            href = quote.xpath('./span[@class="cont_tit"]/font[@class="cont_tit03"]/a/@href').extract_first()
            title = quote.xpath('./span[@class="cont_tit"]/font[@class="cont_tit03"]/a/text()').extract_first()
            if href is not None and title is not None:
                # print u'标题',title
                name = re.findall(ur"\d{4}年\d+月份\d+.*?住宅.*?",title)
                if len(name) > 0:
                    # if href == 'http://www.stats.gov.cn/tjsj/zxfb/201611/t20161118_1430920.html':
                    yield scrapy.Request(href, callback = self.getIndex,meta={'title':title})

        """
        解析下一个网页的所有链接
        """      
        # print u'执行parse的url',response.url         
        next_page_url = response.xpath(u'//li/dl/a[@class="next-page"]/@href').extract_first()
        urlhead = 'http://www.stats.gov.cn/was5/web/'
        # print u"下一个网页",urlhead+next_page_url
        if next_page_url is not None:
            #此时应该可以配置headers等参数
            yield scrapy.Request(urlhead+next_page_url, meta={
                    'splash': {
                        'args': {
                        # set rendering arguments here
                            'html': 1,
                            'png': 1,
                            'wait':2,
                        },
                       
                    }
            })

    #处理得到城市第三个元素即当月的环比指数
    def getIndex(self, response):
        #找到合适的值
        item = HousewaveItem()
        lists  = response.xpath('//table[@class="MsoNormalTable"]')
        title = response.meta['title']
        year =  re.findall(r"\d+",title)[0]
        month = re.findall(r"\d+",title)[1]


        # print u'链接地址',response.url
        """
        遍历该网页中所有的表格
        """
        for i in range(len(lists)):
            # 70个大中城市新建住宅价格指数
            table_title = lists[i].xpath('.//tbody/tr[1]/td/p/b/span/text()').extract()
            # print u'表头',table_title
            if len(table_title) > 0:
                """
                找到数据的开始行
                """
                name = re.findall(ur"大中城市新建商品住宅价格指数|大中城市二手住宅价格指数",table_title[-1])

                irow = 1 # 对每个表的行计数
                # print u'表头==',name
                if len(name)>0:
                    # print u'name表格标题',name
                    if ('大中城市新建商品住宅价格指数' in  name[0]) == True:
                        dataType = 'new'
                    if ('大中城市二手住宅价格指数' in name[0])==True:
                        dataType = 'old'
                        # break
                    # print u'name表格标题',dataType

                    #找到北京所在的行开始往下找
                    allrows = lists[i].xpath('.//tbody/tr')
                    # print u"数据",dataType,allrows
                    if allrows is not None:
                        for row in allrows:
                            row = row.xpath('./td/p/span/text()').extract()
                            # print u"行数据",row
                            rowinfo = self.deal_key(row)
                            if ('北京' in rowinfo or '北' in rowinfo) == True:
                                break
                            irow += 1

                        # print u"北京姑",irow

                        """
                        提取每行的数据

                        """
                        path ='.//tbody/tr[position()>=' + str(irow) + ']'
                        allrows = lists[i].xpath(path)
                        # print u"数据",dataType,irow
                        for erow in allrows:
                            #'./td/p/span/text()|./td/p/span/font/text()' #兼容2015-5,7,9
                            path = './td[position()<=4]/p/span/text()|./td[position()<=4]/p/span/font/text()'
                            rowinfo = erow.xpath(path).extract()
                            # print 'rowinfo',rowinfo
                            key,value = self.deal_info(rowinfo[:-3],rowinfo[-3:][0])
                            # print rowinfo
                            # print u'城市',key
                            if '北'==key:
                                key = '北京'

                            item['city'] = key
                            item['index'] = value
                            item['types'] = dataType
                            item['year'] = year
                            item['month'] = month
                            yield item

                            path = './td[position()>4]/p/span/text()|./td[position()>4]/p/span/font/text()'
                            rowinfo = erow.xpath(path).extract()
                            key,value = self.deal_info(rowinfo[:-3],rowinfo[-3:][0])
                            item['city'] = key
                            item['index'] = value
                            item['types'] = dataType
                            item['year'] = year
                            item['month'] = month
                            yield item


    def getItem(key, value, dataType, year, month):

        ##return every item instance
        item = HousewaveItem()

        item['city'] = key
        item['index'] = value
        item['types'] = dataType
        item['year'] = year
        item['month'] = month
        yield item

    def deal_key(self, key):
        keys = ''
        for k in key:
            keys += k

        # print u'二手房房价',re.findall(ur"<a.*?infodesc .*?>.*?[\u4e00-\u9fa5]+.*?<\/a>",str)
        keys = re.findall(ur"[\u4e00-\u9fa5]+",keys)
        cz = ''
        for k in keys:
            cz += k
        return cz


    def deal_info(self, key, value):
        # print key, value
        keys = ''
        for k in key:
            keys += k

        # print u'二手房房价',re.findall(ur"<a.*?infodesc .*?>.*?[\u4e00-\u9fa5]+.*?<\/a>",str)
        keys = re.findall(ur"[\u4e00-\u9fa5]+",keys)
        cz = ''
        for k in keys:
            cz += k
        # print u'键',key
        # print u'值',value
        # print u'key主键',keys
        value = float(value)
        return cz, value

#要弄懂scrapy中的 item到底怎么用？
# http://www.runoob.com/xpath/xpath-syntax.html
# http://blog.csdn.net/zcc_0015/article/details/52274996
# http://blog.csdn.net/haipengdai/article/details/48654083
# https://segmentfault.com/q/1010000003814607
# http://izhaoyi.top/about/

#http://www.cnblogs.com/zhonghuasong/p/5976003.html
#http://blog.csdn.net/zistxym/article/details/42918339
#解决docker安装问题
#https://segmentfault.com/q/1010000007206051/a-1020000007219088
# http://jingyan.baidu.com/article/2c8c281db408940008252a02.html
#日志问题

#http://www.stats.gov.cn/tjsj/zxfb/201501/t20150118_670296.html
#上个网页的数据出现第一列竟然找不到北京两个字
#http://www.stats.gov.cn/tjsj/zxfb/201404/t20140418_541217.html
#这个数据有问题