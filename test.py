import socketio
import json
import time
import requests
import uuid
import queue
import threading

# สร้าง Socket.IO client โดยเปิด logger เฉพาะที่จำเป็น
sio = socketio.Client(logger=True)

# กำหนดตัวจัดการเหตุการณ์
@sio.event
def connect():
    print("เชื่อมต่อกับเซิร์ฟเวอร์สำเร็จ")
    # ส่งข้อมูลการเข้าร่วมห้อง
    user_id = "678f61a36c184a338cf7ce50"
    data = json.dumps({"userId": user_id})
    sio.emit('join:all:rooms', data)
    print("ส่งคำขอเข้าร่วมห้องเรียบร้อย")

@sio.event
def disconnect():
    print("ตัดการเชื่อมต่อจากเซิร์ฟเวอร์")

@sio.event
def connect_error(data):
    print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {data}")

def send_message(session_id, content):
    try:
        # ตั้งค่า headers
        headers = {
            'User-Agent': 'com.snocko.goochat.sit',
            'Accept': 'application/json',
            'Platform': 'android',
            'App-Version': '1.10.0',
            'Authorization': f'Bearer {token}',
            'Accept-Language': 'en',
            'Device-Id': '8087d25181190bbf',
            'Device-Model': 'Samsung SM-A235F',
            'Device-OS': '14 UPSIDE_DOWN_CAKE',
            'Os-Version': '34.0',
            'Msg-Version': '1',
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept-Encoding': 'gzip'
        }

        # สร้าง GUID ใหม่
        reference_key = str(uuid.uuid4())

        # สร้างข้อมูลที่จะส่ง
        message_data = {
            "sessionId": session_id,
            "referenceKey": reference_key,
            "contentType": "TEXT",
            "content": content,
            "destructTime": 0
        }

        # ส่งข้อความไปยังเซิร์ฟเวอร์ โดยปิดการตรวจสอบ SSL
        response = requests.post(
            'https://sit.apigoochat.net/gochat/v1/chat/send',
            headers=headers,
            json=message_data,
            verify=False  # ปิดการตรวจสอบ SSL
        )

        if response.status_code == 200:
            print("ส่งข้อความตอบกลับสำเร็จ")
        else:
            print(f"เกิดข้อผิดพลาดในการส่งข้อความ: {response.status_code}")
            
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความ: {str(e)}")
        import traceback
        traceback.print_exc()

# เพิ่มตัวแปรเก็บ cache ของข้อความที่เคยตอบไปแล้ว
message_cache = {}
# สร้าง Queue สำหรับเก็บข้อความที่รออยู่
message_queue = queue.Queue()
# สร้างตัวแปรเก็บสถานะการประมวลผล
is_processing = False
# สร้าง Event สำหรับควบคุมการประมวลผล
processing_event = threading.Event()

def process_message_queue():
    global is_processing
    while True:
        try:
            # รอจนกว่าจะได้รับสัญญาณให้ประมวลผลข้อความถัดไป
            processing_event.wait()
            
            # รอรับข้อความจาก Queue
            message_data = message_queue.get()
            session_id = message_data['session_id']
            message = message_data['message']
            
            # ตั้งค่าสถานะกำลังประมวลผล
            is_processing = True
            
            # ตรวจสอบว่าข้อความนี้เคยตอบไปแล้วหรือไม่
            if message in message_cache:
                print("ข้อความนี้เคยตอบไปแล้ว กำลังส่งคำตอบเดิม...")
                response_text = message_cache[message]
                send_message(session_id, response_text)
                # ตั้งค่าสถานะประมวลผลเสร็จสิ้น
                is_processing = False
                # ปล่อยให้ประมวลผลข้อความถัดไป
                processing_event.set()
                continue
                
            print(f"\nกำลังประมวลผลข้อความ: {message}")
            
            # ส่งข้อความไปยัง Ollama API
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "llama3.2:3b",
                    "prompt": f"""คุณเป็นผู้ช่วย AI ที่ฉลาด เป็นมิตร และให้คำตอบที่มีประโยชน์

กฎการตอบ:
1. ไม่สั้นไม่ยาวเกินไป
2. ให้คำตอบที่มีประโยชน์และถูกต้อง
3. สามารถอธิบายเพิ่มเติมได้ถ้าจำเป็น แต่ต้องกระชับ
4. ใช้ภาษาที่เป็นธรรมชาติและเป็นมิตร
5. ถ้าเป็นการทักทาย ให้ตอบกลับด้วยความสุภาพ
6. ถ้าเป็นคำถามทางวิชาการ ให้ตอบอย่างมีเหตุผล
7. ถ้าไม่แน่ใจหรือไม่สามารถตอบได้ ให้ตอบว่า "ขออภัย ฉันไม่สามารถตอบคำถามนี้ได้"
8. ห้ามถามกลับหรือตอบวนซ้ำ
9. ห้ามแนะนำตัวเองหรือพูดถึงความสามารถตัวเอง
10. สำหรับคำถามคณิตศาสตร์ ให้ตอบเฉพาะผลลัพธ์เท่านั้น

ข้อความที่ได้รับ: {message}

ตัวอย่างการตอบที่ดี:
- ถ้าได้รับ "สวัสดี" -> "สวัสดีครับ ยินดีให้บริการค่ะ"
- ถ้าได้รับ "1+1" -> "2"
- ถ้าได้รับ "3+9เท่ากับ" -> "12"
- ถ้าได้รับ "วันนี้วันอะไร" -> "วันนี้คือวันศุกร์ครับ"
- ถ้าได้รับ "อากาศร้อนมาก" -> "เข้าใจครับ แนะนำให้ดื่มน้ำเยอะๆ และอยู่ในที่ร่ม"
- ถ้าได้รับ "ทำไมท้องฟ้าสีฟ้า" -> "ท้องฟ้าสีฟ้าเพราะการกระเจิงของแสงในชั้นบรรยากาศครับ"
- ถ้าได้รับ "Python คืออะไร" -> "Python เป็นภาษาโปรแกรมมิ่งที่เรียนรู้ง่ายและใช้งานได้หลากหลาย"

คำตอบที่ต้องการ:""",
                    "stream": False
                },
                verify=False  # เพิ่มบรรทัดนี้เพื่อปิดการตรวจสอบ SSL
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', 'ไม่สามารถประมวลผลได้')
                print(f"คำตอบ: {response_text}")
                
                # บันทึกคำตอบลงใน cache
                message_cache[message] = response_text
                
                # ส่งข้อความตอบกลับไปยังเซิร์ฟเวอร์
                send_message(session_id, response_text)
            else:
                error_msg = f"เกิดข้อผิดพลาดในการเรียกใช้ Ollama API: {response.status_code}"
                print(error_msg)
                send_message(session_id, error_msg)
                
            # ตั้งค่าสถานะประมวลผลเสร็จสิ้น
            is_processing = False
            # ปล่อยให้ประมวลผลข้อความถัดไป
            processing_event.set()
            
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาด: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            is_processing = False
            # ปล่อยให้ประมวลผลข้อความถัดไปแม้เกิดข้อผิดพลาด
            processing_event.set()

# สร้างและเริ่ม thread สำหรับประมวลผลข้อความ
message_processor = threading.Thread(target=process_message_queue, daemon=True)
message_processor.start()
# ตั้งค่า Event ให้พร้อมประมวลผลข้อความแรก
processing_event.set()

def process_with_ollama(message, session_id):
    try:
        print(f"\nกำลังเพิ่มข้อความเข้าคิว: {message}")
        # เพิ่มข้อความลงใน Queue
        message_queue.put({
            'session_id': session_id,
            'message': message
        })
        return "กำลังประมวลผลข้อความ..."
    except Exception as e:
        error_msg = f"เกิดข้อผิดพลาด: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

# จับเหตุการณ์เฉพาะของแอพ
@sio.on('messages:update:*')
def on_messages_update(data):
    try:
        # ดึงข้อมูลข้อความจาก data
        messages_list = data.get('data', [])
        
        for session in messages_list:
            session_id = session.get('sessionId', 'ไม่มี')
            messages = session.get('messages', [])
            
            for message in messages:
                # ตรวจสอบว่าเป็นข้อความจาก Ollama หรือไม่
                sender_id = message.get('senderId', '')
                if sender_id == "678f61a36c184a338cf7ce50":
                    print("ข้ามการประมวลผลข้อความจาก Ollama")
                    continue  # ข้ามการประมวลผลข้อความจาก Ollama
                
                # กรองเฉพาะข้อมูลที่ต้องการ
                filtered_data = {
                    "Session ID": session_id,
                    "Message ID": message.get('messageId', 'ไม่มี'),
                    "ชื่อผู้ส่ง": message.get('displayName', 'ไม่มี'),
                    "เนื้อหา": message.get('content', 'ไม่มี')
                }
                
                # แสดงข้อมูลที่กรองแล้ว
                print("\n=== ข้อมูลข้อความใหม่ ===")
                for key, value in filtered_data.items():
                    print(f"{key}: {value}")
                
                # ประมวลผลข้อความด้วย Ollama
                if filtered_data["เนื้อหา"] != 'ไม่มี':
                    print("\n=== การประมวลผลด้วย Ollama ===")
                    # เพิ่มข้อความลงใน Queue
                    message_queue.put({
                        'session_id': session_id,
                        'message': filtered_data["เนื้อหา"]
                    })
                    print("กำลังประมวลผลข้อความ...")
                
                print("-" * 50)  # แสดงเส้นคั่นระหว่างข้อความ
                
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการประมวลผลข้อความ: {e}")
        import traceback
        traceback.print_exc()

# จับเหตุการณ์ทั่วไป
@sio.on('*')
def catch_all(event, data):
    # แสดงเฉพาะ event ที่ต้องการ
    if event.startswith('messages:update:'):
        print(f"\n=== ข้อความใหม่ ===")
        print(f"Event: {event}")
        # แสดงเฉพาะข้อมูลที่ต้องการ
        if 'data' in data:
            messages_list = data['data']
            for session in messages_list:
                session_id = session.get('sessionId', 'ไม่มี')
                messages = session.get('messages', [])
                for message in messages:
                    # ตรวจสอบว่าเป็นข้อความจาก Ollama หรือไม่
                    sender_id = message.get('senderId', '')
                    if sender_id == "678f61a36c184a338cf7ce50":
                        print("ข้ามการประมวลผลข้อความจาก Ollama")
                        continue  # ข้ามการประมวลผลข้อความจาก Ollama
                        
                    print(f"Session ID: {session_id}")
                    print(f"Message ID: {message.get('messageId', 'ไม่มี')}")
                    print(f"ชื่อผู้ส่ง: {message.get('displayName', 'ไม่มี')}")
                    content = message.get('content', 'ไม่มี')
                    print(f"เนื้อหา: {content}")
                    
                    # ประมวลผลข้อความด้วย Ollama
                    if content != 'ไม่มี':
                        print("\n=== การประมวลผลด้วย Ollama ===")
                        # เพิ่มข้อความลงใน Queue
                        message_queue.put({
                            'session_id': session_id,
                            'message': content
                        })
                        print("กำลังประมวลผลข้อความ...")
                    
                    print("-" * 50)

# เชื่อมต่อกับเซิร์ฟเวอร์
try:
    # ตั้งค่า token
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NVVUlEIjoiZGQ3ODliODQtZWMwMy00MzRiLWFhNmEtM2E2YTNlMjRiYWRlIiwiZGV2aWNlSUQiOiJkZTk1M2IzZS04YzVhLTQ4NTItODMxNC1jZWZmMDlmMTI1NGMiLCJleHAiOjE3NzY5NDU5MjksInVzZXJJRCI6IjY3OGY2MWEzNmMxODRhMzM4Y2Y3Y2U1MCJ9.l5ue6dak9X9WjapU3EUF1Wquf7i_aaIvbyHvLkx9jy8'
    server_url = "https://sit.apigoochat.net"
    
    # ตั้งค่า headers
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    print("กำลังเชื่อมต่อกับเซิร์ฟเวอร์...")
    
    # เชื่อมต่อกับเซิร์ฟเวอร์
    sio.connect(
        server_url,
        socketio_path='socket/socket.io',
        transports=['websocket'],
        headers=headers
    )
    
    print("รอรับข้อความ... (กด Ctrl+C เพื่อหยุด)")
    
    # ส่ง heartbeat เป็นระยะเพื่อรักษาการเชื่อมต่อ
    counter = 0
    while True:
        time.sleep(10)  # รอ 10 วินาที
        counter += 1
        if sio.connected:
            # ส่ง heartbeat ทุก 30 วินาที
            if counter % 3 == 0:
                try:
                    sio.emit('heartbeat', json.dumps({"timestamp": time.time()}))
                except Exception:
                    pass
        
except KeyboardInterrupt:
    print("\nผู้ใช้ยกเลิกการทำงาน")
    
except Exception:
    print("เกิดข้อผิดพลาดในการเชื่อมต่อ")
    
finally:
    # ตัดการเชื่อมต่อเมื่อเสร็จสิ้น
    if hasattr(sio, 'connected') and sio.connected:
        sio.disconnect()

