import sys
import subprocess

# ১. প্রয়োজনীয় প্যাকেজ অটো-ইনস্টল চেকার
required_packages = ["telethon"]
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f">> প্যাকেজ পাওয়া যায়নি, ইনস্টল করা হচ্ছে: {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import asyncio
import json
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.phone import (
    CreateGroupCallRequest,
    JoinGroupCallRequest,
    GetGroupCallRequest,
    GetGroupParticipantsRequest,
    EditGroupCallParticipantRequest,
    DiscardGroupCallRequest,
    LeaveGroupCallRequest
)
from telethon.tl.types import InputGroupCall, DataJSON, InputPeerUser, PeerUser

# ক্রেডেনশিয়াল
API_ID = 32054831
API_HASH = "89fc23d0ff6763a53004996fe0c6cab2"
SESSION_STRING = "1BVtsOMMBu1WGKCnjA_joyvpHQy2oQ3Y9P0Ncgf8JM7OtAkvKxMTPljd1Sg-viJEMP9rPKZynCFNcI5tbaKL25zRHAneu4rcPCC89ninLD0GnYqY35MsFaT-beg9mIrJBiGqiBznlKs4RNwZHMesqMhryDEpNZRa48pzCUUihR05tcJr5L07ooNhPIOPjYC8sSWYa1SNpO68XgeCtbwoJ31EoQvEPP4FcSuDZoLZvaEasK_UV89hf-QZir-x1aPrtfjcmaY2VtutW8Wql5xK-QocrxmopEN4iY_5hxW43YNmC4BY-4p88FfBfQuPWZD3ivs-5Pd1nV5lKwhnRto1Ukp36FMcsrGc="
TARGET_CHANNEL = "DARK67HACK"

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def make_sdp():
    """টেলিগ্রামের ফুল অডিও SDP পে-লোড"""
    s  = random.randint(100000000, 4294967295)
    s2 = random.randint(100000000, 4294967295)
    fp = ':'.join(f'{random.randint(0,255):02X}' for _ in range(32))
    pw = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=22))
    uf = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
    cn = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))
    ms = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=36))
    return json.dumps({
        "fingerprints": [{"hash": "sha-256", "setup": "actpass", "fingerprint": fp}],
        "pwd": pw, "ufrag": uf, "ssrc": s,
        "ssrc-groups": [{"semantics": "FID", "sources": [s, s2]}],
        "sources": {str(s): {"cname": cn, "msid": f"{ms} {ms}a0"}},
    })

async def robust_join(call_input, join_peer):
    """লাইভে যুক্ত হওয়া এবং এরর হ্যান্ডলিং"""
    for _ in range(3):
        try:
            await client(JoinGroupCallRequest(
                call=call_input,
                join_as=join_peer,
                muted=False,
                video_stopped=True,
                params=DataJSON(data=make_sdp())
            ))
            return True
        except Exception as e:
            if "already" in str(e).lower():
                return True
            await asyncio.sleep(1)
    return False

async def main():
    await client.start()
    me = await client.get_me()
    print(f">> অ্যাকাউন্টে সফলভাবে কানেক্ট হয়েছে: {me.first_name}")

    entity = await client.get_entity(TARGET_CHANNEL)
    channel_peer = await client.get_input_entity(entity)
    user_peer = await client.get_input_entity(me)

    unmuted_users = set()

    # মূল 24/7 লাইভ কন্ট্রোল লুপ
    while True:
        try:
            # ১. লাইভ স্ট্যাটাস চেক ও অটো-স্টার্ট
            full_chat = await client(GetFullChannelRequest(channel=channel_peer))
            call = full_chat.full_chat.call

            if not call:
                print(">> লাইভ তৈরি করা হচ্ছে...")
                try:
                    await client(CreateGroupCallRequest(
                        peer=channel_peer,
                        random_id=random.randint(10000, 99999999)
                    ))
                    await asyncio.sleep(2)
                    full_chat_updated = await client(GetFullChannelRequest(channel=channel_peer))
                    call = full_chat_updated.full_chat.call
                    unmuted_users.clear()
                    print(">> লাইভ সফলভাবে চালু হয়েছে!")
                except FloodWaitError as fe:
                    print(f">> টেলিগ্রাম রেট লিমিট: {fe.seconds} সেকেন্ড অপেক্ষা করতে হবে...")
                    await asyncio.sleep(fe.seconds + 2)
                    continue
                except Exception as e:
                    print(f">> লাইভ চালু করতে সমস্যা: {e}")
                    await asyncio.sleep(4)
                    continue

            call_input = InputGroupCall(id=call.id, access_hash=call.access_hash)

            # ২. লাইভে প্রথমবার জয়েন করা
            print(">> লাইভের ভেতর স্থায়ীভাবে জয়েন করা হচ্ছে...")
            joined = await robust_join(call_input, user_peer)
            if joined:
                print(">> আইডি সফলভাবে লাইভে প্রবেশ করেছে এবং সার্বক্ষণিক গার্ড চালু আছে।")

            # ৩. লাইভে বসে থাকা, ড্রপ হলে রি-জয়েন এবং অটো-আনমিউট লুপ
            while True:
                try:
                    participants_data = await client(GetGroupParticipantsRequest(
                        call=call_input,
                        ids=[],
                        sources=[],
                        offset="",
                        limit=100
                    ))

                    users_dict = {u.id: u for u in getattr(participants_data, 'users', [])}
                    is_me_present = False

                    for p in participants_data.participants:
                        # নিজে লাইভে আছে কিনা যাচাই
                        if isinstance(p.peer, PeerUser) and p.peer.user_id == me.id:
                            if not p.left:
                                is_me_present = True
                            continue

                        user_key = getattr(p, 'source', None) or (p.peer.user_id if isinstance(p.peer, PeerUser) else None)

                        # নতুন ইউজারকে আনমিউট করা
                        if p.muted and user_key not in unmuted_users:
                            try:
                                if isinstance(p.peer, PeerUser):
                                    u = users_dict.get(p.peer.user_id)
                                    input_user = InputPeerUser(user_id=u.id, access_hash=u.access_hash) if u else await client.get_input_entity(p.peer.user_id)
                                else:
                                    input_user = await client.get_input_entity(p.peer)

                                await client(EditGroupCallParticipantRequest(
                                    call=call_input,
                                    participant=input_user,
                                    muted=False
                                ))
                                unmuted_users.add(user_key)
                                print(f">> মেম্বার আনমিউট হয়েছে: {getattr(p.peer, 'user_id', p.peer)}")
                            except FloodWaitError as fwe:
                                await asyncio.sleep(fwe.seconds + 1)
                            except Exception:
                                pass

                    # কোনো কারণে আইডি লাইভ থেকে ছিটকে গেলে তাৎক্ষণিক রি-জয়েন
                    if not is_me_present:
                        print(">> আইডি ড্রপ লক্ষ্য করা গেছে! সাথে সাথে লাইভে পুনরায় রি-জয়েন করা হচ্ছে...")
                        await robust_join(call_input, user_peer)

                    await asyncio.sleep(2)

                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    # কলটি যদি বন্ধ হয়ে গিয়ে থাকে বা নেটওয়ার্ক বিচ্ছিন্ন হয়
                    print(">> লাইভ সেশন চেক করা হচ্ছে...")
                    await asyncio.sleep(3)
                    break

        except KeyboardInterrupt:
            print("\n>> স্ক্রিপ্ট বন্ধ করা হচ্ছে...")
            try:
                if call:
                    call_input = InputGroupCall(id=call.id, access_hash=call.access_hash)
                    await client(LeaveGroupCallRequest(call=call_input))
                    await client(DiscardGroupCallRequest(call=call_input))
                print(">> লাইভ বন্ধ করা হয়েছে।")
            except Exception:
                pass
            break
        except Exception as err:
            print(f">> ত্রুটি: {err}")
            await asyncio.sleep(4)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
