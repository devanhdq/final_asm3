import scrapy
import re


class CovidSpider(scrapy.Spider):
    name = "covid"
    start_urls = ['https://web.archive.org/web/20210907023426/https://ncov.moh.gov.vn/vi/web/guest/dong-thoi-gian']

    # hàm convert trường time theo định dạng hh-mm dd-mm-yyyy
    def reformat_date(self, date_string):
        from datetime import datetime
        date_object = datetime.strptime(date_string, "%H:%M %d/%m/%Y")
        return date_object.strftime("%H:%M %d-%m-%Y")

    #  hàm thay thế các chữ tiếng việt
    def no_accent_vietnamese(self, s):
        s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
        s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
        s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
        s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
        s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
        s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
        s = re.sub(r'[ìíịỉĩ]', 'i', s)
        s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
        s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
        s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
        s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
        s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
        s = re.sub(r'[Đ]', 'D', s)
        s = re.sub(r'[đ]', 'd', s)

        marks_list = [u'\u0300', u'\u0301', u'\u0302', u'\u0303', u'\u0306', u'\u0309', u'\u0323']

        for mark in marks_list:
            s = s.replace(mark, '')
        return s

    # hàm xử lý trường case
    def handles_case(self, case_raw):
        regex = r'\d+\.\d+|\d+'

        case_raw = re.findall(regex, case_raw)
        if len(case_raw) > 0:
            case_raw = int(case_raw[0].replace('.', ''))
        return case_raw

    # hàm xử lý trường detail
    def handle_detail(self, detail):
        regex = r'(\b[A-Z][\w\s]+\b)\s*\((\d+(?:\.\d+)?)\)\s*'
        result = []
        matches = re.findall(regex, detail)
        for match in matches:
            result.append({"city": match[0], "case": match[1]})
        return result

    # hàm xử lý dữ liệu sau khi crawl
    # Xử lý dữ liệu ở trang hiện tại
    # Lấy ra 3 thông tin gồm: date(ngày), case(số ca bệnh trong ngày), detail(danh sách ca bệnh theo từng tỉnh)
    def parse(self, response):

        total_case_raw = response.css('.timeline-sec ul')
        for item in total_case_raw:
            time = self.no_accent_vietnamese(self.reformat_date(item.css(".timeline-head h3::text").get()))
            case_raw = self.no_accent_vietnamese(item.css(".timeline-content p:nth-child(2)::text").get())
            detail_raw = self.no_accent_vietnamese(item.css(".timeline-content p:nth-child(3)").get())
            yield {
                "time": time,
                "new_case": self.handles_case(case_raw),
                "city_case": self.handle_detail(detail_raw)
            }

        # lấy ra button "Tiếp theo"
        next_page = response.css('.lfr-pagination-buttons > li:nth-child(2) > a::attr(href)').get()
        print(next_page)
        # kiểm tra xem nút "Tiếp theo" có khả dụng không, nếu có thì nhấn vào nút đó và cập nhật lại URL mới
        if next_page is not None:
            next_page_url = next_page
            yield response.follow(next_page_url, callback=self.parse)
