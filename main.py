import os
import sys
import time
import pandas as pd
import datetime
import schedule
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# ChromeDriver 경로 설정
CHROME_DRIVER_PATH = "C:/resource/chromedriver-win64/chromedriver-win64/chromedriver.exe"

# ✅ StockExchangeScraper: 객체
class StockExchangeScraper:
    _instance = None  # 싱글톤 인스턴스 저장

    def __new__(cls):
        """싱글톤 패턴 적용: 인스턴스가 없을 때만 생성"""
        if cls._instance is None:
            cls._instance = super(StockExchangeScraper, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def __init__(self):
        self.exchange_data = None

    def _initialize(self):
        """WebDriver 설정 및 실행"""
        options = Options()
        options.add_experimental_option("detach", True)  # 브라우저 자동 종료 방지
        options.add_argument("--start-maximized")  # 창 최대화
        options.add_argument("--disable-popup-blocking")  # 팝업 차단 방지
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
        self.wait = WebDriverWait(self.driver, 15)  # 최대 15초 대기
        self.stock_data_list = []  # 여러 개의 주식 데이터를 저장할 리스트

    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스 반환"""
        return cls()

    def get_stock_data(self, stock_code):
        """네이버 금융에서 특정 종목 주식 데이터 크롤링"""
        stock_url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        print(f"🔍 크롤링 시작: {stock_code} ({stock_url})")
        self.driver.get(stock_url)
        time.sleep(3)

        try:
            # ✅ 페이지 내에 데이터가 있는지 확인
            if "종목명" not in self.driver.page_source:
                print(f"⚠️ [{stock_code}] 페이지에 데이터가 없음 (비상장/관리종목 가능성)")
                return

            print(f"✅ [INFO] [{stock_code}] 페이지 로딩 완료. 데이터 추출 시작...")

            # ✅ 종목명 가져오기
            stock_name = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".wrap_company h2 a"))
            ).text
            print(f"🔎 [DEBUG] 종목명 추출 성공: {stock_name}")

            # ✅ 날짜 데이터 가져오기
            date_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".description .date"))
            ).text.strip()
            print(f"🔎 [DEBUG] 기준 날짜 추출 성공: {date_element}")

            # ✅ 현재가 가져오기 (상승/하락 구분)
            price_elements_up = self.driver.find_elements(By.CSS_SELECTOR, ".no_today em.no_up span")
            price_elements_down = self.driver.find_elements(By.CSS_SELECTOR, ".no_today em.no_down span")

            if price_elements_up:
                print(f"🔎 [DEBUG] 상승장에서 현재가 추출 시도...")
                current_price = "".join([span.text for span in price_elements_up])
            elif price_elements_down:
                print(f"🔎 [DEBUG] 하락장에서 현재가 추출 시도...")
                current_price = "".join([span.text for span in price_elements_down])
            else:
                print(f"⚠️ [WARN] 현재가를 찾을 수 없음!")
                current_price = "N/A"

            print(f"🔎 [DEBUG] 현재가 추출 성공: {current_price}")

            # ✅ 등락가 및 변동률 가져오기 (상승/하락 모두 고려)
            # 등락가 및 변동률 기본값 설정 (초기화)
            change_number = "N/A"
            change_percent = "N/A"
            try:
                # 상승장인 경우
                up_elements = self.driver.find_elements(By.CSS_SELECTOR, ".no_exday em.no_up")
                down_elements = self.driver.find_elements(By.CSS_SELECTOR, ".no_exday em.no_down")

                if up_elements:
                    # 상승 등락가
                    change_number_element = up_elements[0].find_elements(By.CSS_SELECTOR, "span:not(.ico)")
                    change_number = "".join([span.text for span in change_number_element if span.text.strip()])

                    # 상승 변동률
                    change_percent_element = up_elements[1].find_elements(By.CSS_SELECTOR, "span:not(.ico)")
                    change_percent = "".join([span.text for span in change_percent_element if span.text.strip()])

                    print(f"🔎 [DEBUG] 상승 등락가: {change_number}")
                    print(f"🔎 [DEBUG] 상승 변동률: {change_percent}")

                elif down_elements:
                    # 하락 등락가
                    change_number_element = down_elements[0].find_elements(By.CSS_SELECTOR, "span:not(.ico)")
                    change_number = "".join([span.text for span in change_number_element if span.text.strip()])
                    change_number = "-" + change_number  # 하락이면 음수로 변환

                    # 하락 변동률
                    change_percent_element = down_elements[1].find_elements(By.CSS_SELECTOR, "span:not(.ico)")
                    change_percent = "".join([span.text for span in change_percent_element if span.text.strip()])
                    change_percent = "-" + change_percent  # 하락이면 음수로 변환

                    print(f"🔎 [DEBUG] 하락 등락가: {change_number}")
                    print(f"🔎 [DEBUG] 하락 변동률: {change_percent}")

                else:
                    print("⚠️ [WARN] 등락 데이터 없음")
                    change_number, change_percent = "N/A", "N/A"

            except Exception as e:
                print(f"❌ [ERROR] 등락 데이터 크롤링 오류: {e}")

            # ✅ 거래량 가져오기
            volume_elements = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//span[contains(text(), '거래량')]/following-sibling::em/span"))
            )
            volume = "".join([span.text for span in volume_elements])
            print(f"🔎 [DEBUG] 거래량 추출 성공: {volume}")

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
            print(f"❌ [ERROR] 주식 데이터 크롤링 오류 ({stock_code}): {e}")

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



# ✅ GUI 클래스
class StockCrawlerGUI:
    def __init__(self):
        """GUI 초기화"""

        self.root = tk.Tk()
        self.root.title("📈 주식 크롤링 프로그램")
        self.root.geometry("800x550")
        self.root.resizable(False, False)

        # ✅ 실행 상태 변수
        self.is_running = False
        self.stop_event = threading.Event()

        # ✅ 스타일 적용
        self.configure_styles()

        # ✅ GUI 구성 요소 생성
        self.create_widgets()

        # ✅ GUI 실행
        self.root.mainloop()

        # ✅ GUI 위젯의 속성들을 미리 선언 (가독성과 코드 유지보수를 위해 사용)
        self.scrollbar = None  # 리스트박스의 스크롤바
        self.listbox = None  # 주식 검색 결과를 표시하는 리스트박스
        self.btn_search = None  # 검색 버튼
        self.stock_entry = None  # 주식 검색 입력 필드
        self.btn_exit = None  # 프로그램 종료 버튼
        self.btn_stop = None  # 자동 실행 중지 버튼
        self.btn_start = None  # 자동 실행 시작 버튼
        self.lbl_status = None  # 실행 상태 표시 라벨

    @staticmethod
    def configure_styles():
        """GUI 스타일을 설정"""
        style = ttk.Style()
        style.theme_use("clam")  # ✅ 모던한 테마 적용

        # ✅ 버튼 스타일 설정
        style.configure("TButton", font=("Arial", 11), padding=5)

        # ✅ 실행 상태 라벨 스타일
        style.configure("Status.TLabel", font=("Arial", 12, "bold"))

        # ✅ 입력 필드 스타일
        style.configure("TEntry", padding=5, font=("Arial", 11))

        # ✅ 프레임 배경색 설정
        style.configure("TFrame", background="#f8f9fa")

    def create_widgets(self):
        """GUI 위젯 생성 및 배치"""
        # ✅ 실행 상태 라벨
        self.lbl_status = ttk.Label(self.root, text="🔴 실행 안 됨", style="Status.TLabel", foreground="red")
        self.lbl_status.pack(pady=10)

        # ✅ 버튼 프레임
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5)

        self.btn_start = ttk.Button(button_frame, text="▶ 자동 실행 시작", command=self.start_scheduler)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = ttk.Button(button_frame, text="⏸ 실행 중지", command=self.stop_scheduler, state=tk.DISABLED)
        self.btn_stop.grid(row=0, column=1, padx=5)

        self.btn_exit = ttk.Button(button_frame, text="⛔ 완전 종료", command=self.exit_program)
        self.btn_exit.grid(row=0, column=2, padx=5)

        # ✅ 주식 검색 필드
        search_frame = ttk.Frame(self.root)
        search_frame.pack(pady=5)

        ttk.Label(search_frame, text="🔍 주식 종목 검색:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5)
        self.stock_entry = ttk.Entry(search_frame, width=25)
        self.stock_entry.grid(row=0, column=1, padx=5)

        self.btn_search = ttk.Button(search_frame, text="검색", command=self.search_and_crawl)
        self.btn_search.grid(row=0, column=2, padx=5)

        # ✅ 검색된 주식 리스트
        listbox_frame = ttk.Frame(self.root)
        listbox_frame.pack(pady=10)

        self.listbox = tk.Listbox(listbox_frame, height=8, width=50)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.listbox.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", self.select_stock)

    def start_scheduler(self):
        """스케줄러 실행"""
        if self.is_running:
            messagebox.showwarning("경고", "이미 실행 중입니다!")
            return

        self.is_running = True
        self.stop_event.clear()

        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text="🔵 실행 중...", foreground="blue")

        # ✅ run_scheduler()를 실행할 때, 현재 GUI 인스턴스를 전달
        thread = threading.Thread(target=run_scheduler, args=(self,), daemon=True)
        thread.start()
        messagebox.showinfo("알림", "백그라운드에서 자동 실행이 시작되었습니다!")

    def stop_scheduler(self):
        """스케줄러 정지"""
        self.is_running = False
        self.stop_event.set()

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="🔴 실행 중지됨", foreground="red")
        messagebox.showinfo("알림", "스케줄러 실행이 중지되었습니다!")

    def exit_program(self):
        """프로그램 종료"""
        self.is_running = False
        self.stop_event.set()
        print("🛑 프로그램 완전 종료")
        sys.exit(0)  # 시스템 종료

    def search_and_crawl(self):
        """주식 검색 후 크롤링 실행"""
        selected_stock = self.stock_entry.get()

        try:
            stock_df = pd.read_csv("kospi_stock_codes.csv", dtype={'종목코드': str})
        except FileNotFoundError:
            messagebox.showerror("파일 오류", "kospi_stock_codes.csv 파일이 없습니다.")
            return

        matched_rows = stock_df[stock_df["종목명"].str.contains(selected_stock, na=False)]

        if matched_rows.empty:
            messagebox.showwarning("검색 실패", "해당 종목을 찾을 수 없습니다.")
        elif len(matched_rows) > 1:
            self.listbox.delete(0, tk.END)
            for _, row in matched_rows.iterrows():
                self.listbox.insert(tk.END, f"{row['종목명']} ({row['종목코드']})")
        else:
            stock_code = matched_rows.iloc[0]["종목코드"]
            self.stock_entry.delete(0, tk.END)
            self.stock_entry.insert(0, stock_code)
            messagebox.showinfo("검색 성공", f"종목 코드: {stock_code}")
            crawl_and_save(stock_code)

    def select_stock(self, event=None):
        """리스트에서 선택한 주식 종목 크롤링"""
        try:
            selected = self.listbox.get(self.listbox.curselection())
            stock_code = selected.split("(")[-1].strip(")")
            self.stock_entry.delete(0, tk.END)
            self.stock_entry.insert(0, stock_code)
            messagebox.showinfo("선택 완료", f"선택된 종목 코드: {stock_code}")
            crawl_and_save(stock_code)
        except IndexError:
            return  # 리스트에서 아무것도 선택하지 않았을 때 오류 방지



# ✅ KOSPI 주식 코드 크롤링
def get_kospi_stock_codes():
    """네이버 금융에서 KOSPI 주식 코드 목록 크롤링"""
    url = "https://finance.naver.com/sise/sise_market_sum.nhn?sosok=0"
    options = Options()
    options.add_argument("--headless")  # 브라우저 창 안 띄움
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    driver.get(url)
    time.sleep(3)

    stock_data = []
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "#contentarea table.type_2 tbody tr")
        for row in rows:
            try:
                name = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a").text
                stock_code = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a").get_attribute("href").split("=")[-1]
                stock_data.append({"종목명": name, "종목코드": stock_code})
            except NoSuchElementException:
                print("⚠️ 일부 주식 코드 요소를 찾을 수 없습니다. 건너뜀.")
                continue
    except TimeoutException:
        print("❌ 페이지 로딩 시간이 초과되었습니다.")
    except WebDriverException as e:
        print(f"❌ Selenium WebDriver 오류 발생: {e}")
    except Exception as e:
        print(f"❌ 알 수 없는 오류 발생: {e}")

    driver.quit()

    df = pd.DataFrame(stock_data)
    df.to_csv("kospi_stock_codes.csv", index=False, encoding="utf-8-sig")
    print("✅ KOSPI 주식 코드 리스트 저장 완료: kospi_stock_codes.csv")


# ✅ 크롤링 & CSV 저장 함수 (중복 제거)
def crawl_and_save(stock_code):
    scraper = StockExchangeScraper.get_instance()

    print(f"📌 [{stock_code}] 주식 데이터 크롤링 시작...")
    scraper.get_stock_data(stock_code)
    print(f"✅ [{stock_code}] 주식 데이터 크롤링 완료!")

    print("📌 환율 데이터 크롤링 시작...")
    scraper.get_exchange_rate()
    print("✅ 환율 데이터 크롤링 완료!")

    print("📌 CSV 저장 시작...")
    scraper.save_to_csv()
    print("✅ CSV 저장 완료!")



# 자동화를 위해서 종목코드 stocks.txt에 기입해야함
def auto_crawl():
    """stocks.txt에서 종목 코드를 불러와 자동으로 크롤링"""
    scraper = StockExchangeScraper.get_instance()  # ✅ 싱글톤 객체 가져오기
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"📌 [AUTO] {now} - 스케줄 실행 중...")

    if not os.path.exists("stocks.txt"):
        print(f"⚠️ [{now}] stocks.txt 파일이 없음! 자동 크롤링 건너뜀")
        return

    with open("stocks.txt", "r", encoding="utf-8") as file:
        stock_codes = [line.strip() for line in file.readlines() if line.strip()]

    if not stock_codes:
        print(f"⚠️ [{now}] stocks.txt에 종목 코드가 없음! 자동 크롤링 건너뜀")
        return

    for stock_code in stock_codes:
        print(f"🔍 [{now}] {stock_code} 크롤링 시작...")
        scraper.get_stock_data(stock_code)  # ✅ 종목별 주가 크롤링
        scraper.get_exchange_rate()  # ✅ 환율 데이터도 함께 가져오기

        if scraper.stock_data_list:
            # ✅ 모든 데이터에 환율 정보 추가
            for data in scraper.stock_data_list:
                for key, value in scraper.exchange_data.items():
                    data[key] = value

            # ✅ 데이터 저장
            scraper.save_to_csv()  # 👉 기존의 중복된 CSV 저장 로직 대신 save_to_csv() 함수 호출

            # ✅ 리스트 초기화 (다음 종목을 위해)
            scraper.stock_data_list = []

    print(f"✅ [{now}] 자동 크롤링 완료!")

# ✅ 스케줄러 실행 함수
def run_scheduler(gui_instance):
    """스케줄러 백그라운드 실행"""
    while gui_instance.is_running:  # ✅ GUI에서 상태 확인
        if gui_instance.stop_event.is_set():  # ✅ 종료 신호 감지 시 루프 종료
            break
        print(f"⌛ [SCHEDULER] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 실행 대기 중...")
        schedule.run_pending()
        time.sleep(30)

# ✅ 스케줄 등록
schedule.every().day.at("09:00").do(auto_crawl)
schedule.every().day.at("09:30").do(auto_crawl)
schedule.every().day.at("15:00").do(auto_crawl)
schedule.every().day.at("18:00").do(auto_crawl)

# 종목 코드 CSV 파일이 없으면 크롤링 실행
if not os.path.exists("kospi_stock_codes.csv"):
    print("Kospi Code CSV 파일 없음으로 크롤링 시작")
    get_kospi_stock_codes()
else:
    print("Kospi Code CSV 파일 존재 확인")

# ✅ 실행 상태 변수
is_running = False
stop_event = threading.Event()

# ✅ GUI 실행
if __name__ == "__main__":
    StockCrawlerGUI()