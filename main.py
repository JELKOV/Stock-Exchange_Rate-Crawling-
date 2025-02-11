import os
import time
import pandas as pd
import datetime
import schedule
import threading
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ChromeDriver 경로 설정
CHROME_DRIVER_PATH = "C:/resource/chromedriver-win64/chromedriver-win64/chromedriver.exe"

# ✅ Scraper 객체 생성
scraper = None  # 전역 변수로 설정 (필요할 때만 생성)

# ✅ StockExchangeScraper: 객체
class StockExchangeScraper:
    def __init__(self):
        """WebDriver 설정 및 실행"""
        options = Options()
        options.add_experimental_option("detach", True)  # 브라우저 자동 종료 방지
        options.add_argument("--start-maximized")  # 창 최대화
        options.add_argument("--disable-popup-blocking")  # 팝업 차단 방지
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
        self.wait = WebDriverWait(self.driver, 15)  # 최대 15초 대기
        self.stock_data_list = []  # 여러 개의 주식 데이터를 저장할 리스트
        self.exchange_data = {}

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

def create_scraper():
    """WebDriver 인스턴스 생성"""
    global scraper
    if scraper is None:
        print("🔵 WebDriver 인스턴스 생성 중...")
        scraper = StockExchangeScraper()
        if scraper is not None:
            print("✅ WebDriver 인스턴스 생성 완료!")
        else:
            print("❌ WebDriver 생성 실패!")

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
            except:
                continue
    except Exception as e:
        print(f"❌ 코스피 주식 코드 크롤링 오류: {e}")

    driver.quit()

    df = pd.DataFrame(stock_data)
    df.to_csv("kospi_stock_codes.csv", index=False, encoding="utf-8-sig")
    print("✅ KOSPI 주식 코드 리스트 저장 완료: kospi_stock_codes.csv")


# ✅ 크롤링 & CSV 저장 함수 (중복 제거)
def crawl_and_save(stock_code):
    global scraper  # 전역 변수 사용 선언

    # ✅ `scraper`가 없으면 자동으로 생성
    if scraper is None:
        create_scraper()

    print(f"📌 [{stock_code}] 주식 데이터 크롤링 시작...")
    scraper.get_stock_data(stock_code)
    print(f"✅ [{stock_code}] 주식 데이터 크롤링 완료!")

    print("📌 환율 데이터 크롤링 시작...")
    scraper.get_exchange_rate()
    print("✅ 환율 데이터 크롤링 완료!")

    print("📌 CSV 저장 시작...")
    scraper.save_to_csv()
    print("✅ CSV 저장 완료!")


# ✅ GUI: 주식 코드 검색 + 크롤링 실행 기능 추가
def search_and_crawl():
    """사용자가 입력한 종목명으로 검색 후 주식 데이터 크롤링"""
    global scraper  # 전역 변수 사용 선언
    selected_stock = stock_entry.get()

    stock_df = pd.read_csv("kospi_stock_codes.csv", dtype={'종목코드': str})
    matched_rows = stock_df[stock_df["종목명"].str.contains(selected_stock, na=False)]

    # ✅ 검색된 결과가 여러 개일 경우 리스트박스에 표시
    if matched_rows.empty:
        messagebox.showwarning("검색 실패", "해당 종목을 찾을 수 없습니다.")
    elif len(matched_rows) > 1:
        listbox.delete(0, tk.END)
        for index, row in matched_rows.iterrows():
            listbox.insert(tk.END, f"{row['종목명']} ({row['종목코드']})")
    else:
        stock_code = matched_rows.iloc[0]["종목코드"]
        stock_entry.delete(0, tk.END)
        stock_entry.insert(0, stock_code)
        messagebox.showinfo("검색 성공", f"종목 코드: {stock_code}")

        # ✅ `scraper` 객체가 없으면 생성
        if scraper is None:
            create_scraper()

        # ✅ 크롤링 실행
        crawl_and_save(stock_code)


# ✅ 종목 선택 후 크롤링 실행 함수
def select_stock(event):
    """리스트박스에서 선택한 주식 종목으로 크롤링"""
    selected = listbox.get(listbox.curselection())  # 선택된 항목 가져오기
    stock_code = selected.split("(")[-1].strip(")")  # 종목 코드 추출
    stock_entry.delete(0, tk.END)
    stock_entry.insert(0, stock_code)

    messagebox.showinfo("선택 완료", f"선택된 종목 코드: {stock_code}")

    # ✅ 통합된 크롤링 함수 실행
    crawl_and_save(stock_code)


# 종목 코드 CSV 파일이 없으면 크롤링 실행
if not os.path.exists("kospi_stock_codes.csv"):
    print("Kospi Code CSV 파일 없음으로 크롤링 시작")
    get_kospi_stock_codes()
else:
    print("Kospi Code CSV 파일 존재 확인")


# 자동화를 위해서 종목코드 stocks.txt에 기입해야함
def auto_crawl():
    """stocks.txt에서 종목 코드를 불러와 자동으로 크롤링"""
    create_scraper()  # scraper 인스턴스 생성
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


# ✅ 스케줄 등록
schedule.every().day.at("09:00").do(auto_crawl)
schedule.every().day.at("09:30").do(auto_crawl)
schedule.every().day.at("15:00").do(auto_crawl)
schedule.every().day.at("18:00").do(auto_crawl)
schedule.every().day.at("19:53").do(auto_crawl)

# ✅ 실행 상태 변수 (스레드 종료 신호)
is_running = False
stop_event = threading.Event()

# ✅ 스케줄러 실행 함수
def run_scheduler():
    """스케줄러 백그라운드 실행"""
    global is_running
    while is_running:
        if stop_event.is_set():  # ✅ 종료 신호 감지 시 루프 종료
            break
        print(f"⌛ [SCHEDULER] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 실행 대기 중...")
        schedule.run_pending()
        time.sleep(30)

# ✅ 스케줄러 시작
def start_scheduler():
    """스케줄러 실행 버튼 핸들러"""
    global is_running, stop_event

    if is_running:
        messagebox.showwarning("경고", "이미 실행 중입니다!")
        return

    is_running = True
    stop_event.clear()  # ✅ 종료 신호 초기화
    btn_start.config(state=tk.DISABLED)
    btn_stop.config(state=tk.NORMAL)
    lbl_status.config(text="🔵 실행 중...", fg="blue")

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    messagebox.showinfo("알림", "백그라운드에서 자동 실행이 시작되었습니다!")

# ✅ 스케줄러 중지
def stop_scheduler():
    """스케줄러 정지 버튼 핸들러"""
    global is_running
    is_running = False
    stop_event.set()  # ✅ 종료 신호 설정
    btn_start.config(state=tk.NORMAL)
    btn_stop.config(state=tk.DISABLED)
    lbl_status.config(text="🔴 실행 중지됨", fg="red")
    messagebox.showinfo("알림", "스케줄러 실행이 중지되었습니다!")

# ✅ 프로그램 종료
def exit_program():
    """완전 종료"""
    global is_running
    is_running = False
    stop_event.set()  # ✅ 종료 신호 설정
    print("🛑 프로그램 완전 종료")
    os._exit(0)  # 강제 종료


# # ✅ 백그라운드 스케줄러 실행
# thread = threading.Thread(target=run_scheduler, daemon=True)
# thread.start()

# ✅ GUI 창 생성
root = tk.Tk()
root.title("주식 크롤링 프로그램")
root.geometry("800x550")  # 창 크기 설정

# ✅ GUI 구성 요소
lbl_status = tk.Label(root, text="🔴 실행 안 됨", fg="red", font=("Arial", 12))
lbl_status.pack(pady=10)

btn_start = tk.Button(root, text="자동 실행 시작", command=start_scheduler, font=("Arial", 12))
btn_start.pack(pady=5)

btn_stop = tk.Button(root, text="실행 중지", command=stop_scheduler, font=("Arial", 12), state=tk.DISABLED)
btn_stop.pack(pady=5)

btn_exit = tk.Button(root, text="완전 종료", command=exit_program, font=("Arial", 12), fg="white", bg="red")
btn_exit.pack(pady=5)

tk.Label(root, text="주식 종목 검색:").pack()
stock_entry = tk.Entry(root)
stock_entry.pack()

tk.Button(root, text="검색", command=search_and_crawl).pack()

# ✅ 검색된 주식 리스트 출력할 리스트박스
listbox = tk.Listbox(root, height=8)
listbox.pack(fill=tk.BOTH, expand=True)
listbox.bind("<<ListboxSelect>>", select_stock)  # 선택 이벤트 추가

# ✅ GUI 실행
root.mainloop()