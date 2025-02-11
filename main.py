import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ChromeDriver 경로 설정
CHROME_DRIVER_PATH = "C:/resource/chromedriver-win64/chromedriver-win64/chromedriver.exe"


def get_stock_codes():
    """네이버 금융에서 주식 코드 목록 크롤링"""
    url = "https://finance.naver.com/sise/sise_market_sum.nhn?sosok=0"  # KOSPI 기준
    options = Options()
    options.add_argument("--headless")  # 브라우저 창 안 띄움
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

    driver.get(url)
    time.sleep(2)

    stock_data = []

    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "#contentarea table.type_2 tbody tr")
        for row in rows:
            try:
                name = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a").text  # 종목명
                code = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a").get_attribute("href").split("=")[
                    -1]  # 종목 코드
                stock_data.append({"종목명": name, "종목코드": code})
            except:
                continue  # 공백 row 제외

    except Exception as e:
        print(f"❌ 주식 코드 크롤링 오류: {e}")

    driver.quit()

    df = pd.DataFrame(stock_data)
    df.to_csv("stock_codes.csv", index=False, encoding="utf-8-sig")
    print("✅ 주식 코드 리스트 저장 완료: stock_codes.csv")




class StockExchangeScraper:
    def __init__(self):
        """WebDriver 설정 및 실행"""
        options = Options()
        options.add_experimental_option("detach", True)  # 브라우저 자동 종료 방지
        options.add_argument("--start-maximized")  # 창 최대화
        options.add_argument("--disable-popup-blocking")  # 팝업 차단 방지

        self.driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
        self.wait = WebDriverWait(self.driver, 10)  # 최대 10초 대기
        self.stock_data_list = []  # 여러 개의 주식 데이터를 저장할 리스트
        self.exchange_data = {}

    def get_stock_data(self, stock_code):
        """네이버 금융에서 특정 종목 주식 데이터 크롤링"""
        stock_url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        self.driver.get(stock_url)
        time.sleep(2)

        try:
            # ✅ 종목명 가져오기
            stock_name = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".wrap_company h2 a"))
            ).text
            print(stock_name)

            # ✅ 날짜 데이터 가져오기
            date_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".description .date"))
            ).text.strip()
            print(f"📅 기준 날짜: {date_element}")

            # ✅ 현재가 (여러 span 태그를 결합)
            price_elements = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".no_today em.no_up span"))
            )
            current_price = "".join([span.text for span in price_elements])
            print(current_price)

            # ✅ 등락가 및 등락률 가져오기
            change_elements = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".no_exday em.no_up span, .no_exday em.no_down span"))
            )
            change_text = "".join([span.text for span in change_elements])  # 예: "상승1,900+3.54%" 또는 "하락900-2.45%"
            print(f"원본 등락률 데이터: {change_text}")

            # ✅ "상승" 또는 "하락" 제거 후 숫자만 추출
            change_number = re.findall(r"\d{1,3}(?:,\d{3})*", change_text)  # 등락 금액 (1,900)
            change_percent = re.findall(r"[-+]?\d+\.\d+%", change_text)  # 변동률 (+3.54%)

            change_number = change_number[0] if change_number else "N/A"
            change_percent = change_percent[0] if change_percent else "N/A"

            # ✅ 거래량 가져오기
            volume_elements = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//span[contains(text(), '거래량')]/following-sibling::em/span"))
            )
            volume = "".join([span.text for span in volume_elements])
            print(volume)

            stock_data = {
                "기준 날짜": date_element,  # 날짜 추가
                "종목명": stock_name,
                "현재가": current_price,
                "등락가": change_number,
                "등락률": change_percent,
                "거래량": volume
            }
            self.stock_data_list.append(stock_data)
            print(f"📊 {stock_name} 데이터 수집 완료: {stock_data}")

        except Exception as e:
            print(f"❌ 주식 데이터 크롤링 오류: {e}")

    def get_exchange_rate(self):
        """네이버 금융에서 환율 데이터 크롤링"""
        exchange_url = "https://finance.naver.com/marketindex/"
        self.driver.get(exchange_url)
        time.sleep(2)

        try:
            # ✅ WebDriverWait으로 요소가 나타날 때까지 대기
            exchange_rate_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#exchangeList .value"))
            )
            change_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#exchangeList .change"))
            )

            # ✅ WebElement에서 `.text` 값을 추출
            exchange_rate = exchange_rate_element.text.strip()
            change = change_element.text.strip()


            # ✅ JavaScript로 변동 방향 (하락/상승) 요소 가져오기
            change_direction = self.driver.execute_script(
                """
                return document.querySelector("#exchangeList .change").nextElementSibling.textContent.trim();
                """
            )
            print(f"변동 방향: {change_direction}")  # 디버깅 확인용


            # ✅ 변동 방향에 따라 부호 추가
            if "하락" in change_direction:
                change = f"-{change}"  # 하락이면 음수
            elif "상승" in change_direction:
                change = f"+{change}"  # 상승이면 양수

            self.exchange_data = {
                "통화": "USD/KRW",
                "현재 환율": exchange_rate,
                "변동률": change
            }
            print(f"💰 환율 데이터 수집 완료: {self.exchange_data}")

        except Exception as e:
            print(f"❌ 환율 데이터 크롤링 오류: {e}")

    def save_to_csv(self, filename="stock_exchange_data.csv"):
        """크롤링한 데이터를 CSV 파일로 저장"""
        if self.stock_data_list:
            df = pd.DataFrame(self.stock_data_list)

            # ✅ 환율 데이터 추가 (모든 주식 데이터 행에 동일하게 추가)
            for key, value in self.exchange_data.items():
                df[key] = value

            # ✅ 기존 CSV 파일 확인 후 이어서 저장 (Append 모드)
            if os.path.exists(filename):
                try:
                    existing_df = pd.read_csv(filename, encoding="utf-8-sig")
                    df = pd.concat([existing_df, df], ignore_index=True)
                except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
                    print("⚠️ 기존 CSV 파일이 손상되었거나 비어 있습니다. 새로 생성합니다.")

            df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"✅ CSV 저장 완료: {filename}")
        else:
            print("⚠️ 저장할 데이터가 없습니다.")

    def close_browser(self):
        """WebDriver 종료"""
        self.driver.quit()
        print("🛑 WebDriver 종료 완료")


# 실행
if __name__ == "__main__":
    scraper = StockExchangeScraper()

    # ✅ 사용자 입력으로 주식 코드 입력 받기
    stock_codes = input("조사할 주식 코드를 ,(쉼표)로 구분하여 입력하세요 (예: 005930, 000660): ")
    stock_code_list = stock_codes.replace(" ", "").split(",")

    # ✅ 입력한 주식 코드별 데이터 수집
    for stock_code in stock_code_list:
        scraper.get_stock_data(stock_code)

    # ✅ 환율 데이터 수집
    scraper.get_exchange_rate()

    # ✅ CSV 저장
    scraper.save_to_csv()

    # # ✅ 브라우저 종료
    # scraper.close_browser()