import socketio
import json
import time

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
                    print(f"Session ID: {session_id}")
                    print(f"Message ID: {message.get('messageId', 'ไม่มี')}")
                    print(f"ชื่อผู้ส่ง: {message.get('displayName', 'ไม่มี')}")
                    print(f"เนื้อหา: {message.get('content', 'ไม่มี')}")
                    print("-" * 50)

# เชื่อมต่อกับเซิร์ฟเวอร์
try:
    # ตั้งค่า token
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NVVUlEIjoiY2ZkNDU4OGYtOThlNC00MTNiLWIzMmQtZTNkMjM5ZGU5ZTQyIiwiZGV2aWNlSUQiOiI4MDg3ZDI1MTgxMTkwYmJmIiwiZXhwIjoxNzc2ODY1MTkyLCJ1c2VySUQiOiI2NzhmNjFhMzZjMTg0YTMzOGNmN2NlNTAifQ.DfnbLiSYl910UNw0qwkCb0IMGbQ8HcZliKaSYy0ek_E'
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

