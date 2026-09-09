import sys
import subprocess

# ১. প্রয়োজনীয় লাইব্রেরি অটো-চেকার ও ইনস্টলার
try:
    import telethon
except ImportError:
    print(">> Telethon লাইব্রেরি ইনস্টল করা হচ্ছে...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon"])

import asyncio
import json
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.phone import (
    JoinGroupCallRequest,
    GetGroupCallRequest,
    GetGroupParticipantsRequest,
    EditGroupCallParticipantRequest,
    LeaveGroupCallRequest
)
from telethon.tl.types import InputGroupCall, DataJSON, InputPeerUser, PeerUser, PeerChannel

# ক্রেডেনশিয়াল
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

async def join_live_call(call_input, join_peer):
    """লাইভে হোস্ট/পার্টিসিপেন্ট হিসেবে জয়েন করা"""
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
    print(f">> অ্যাকাউন্টে লগইন সফল: {me.first_name}")

    entity = await client.get_entity(TARGET_CHANNEL)
    channel_peer = await client.get_input_entity(entity)
    user_peer = await client.get_input_entity(me)

    print(f">> চ্যানেল [{TARGET_CHANNEL}] মনিটরিং শুরু হয়েছে...")
    print(">> লাইভ শুরু হওয়া মাত্রই স্বয়ংক্রিয়ভাবে জয়েন করা হবে।\n")

    while True:
        try:
            # ১. চ্যানেলের লাইভ স্ট্যাটাস চেক করা
            full_chat = await client(GetFullChannelRequest(channel=channel_peer))
            call = full_chat.full_chat.call

            # লাইভ না থাকলে অপেক্ষা করা (নিজে থেকে লাইভ স্টার্ট করবে না)
            if not call:
                await asyncio.sleep(4)
                continue

            print("🟢 লাইভ স্ট্রিম শনাক্ত হয়েছে! জয়েন করার প্রস্তুতি নেওয়া হচ্ছে...")
            call_input = InputGroupCall(id=call.id, access_hash=call.access_hash)

            # ২. হাইড হওয়া এড়াতে চ্যানেল হিসেবে জয়েনের চেষ্টা (না হলে ইউজার প্রোফাইল)
            joined = await join_live_call(call_input, channel_peer)
            active_peer = channel_peer
            if not joined:
                joined = await join_live_call(call_input, user_peer)
                active_peer = user_peer

            if joined:
                print("✅ লাইভে সফলভাবে জয়েন করা হয়েছে এবং সক্রিয় রাখা হয়েছে!")

            unmuted_users = set()

            # ৩. লাইভে বসে থাকা এবং অটো-আনমিউট লুপ
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
                    is_still_in_call = False

                    for p in participants_data.participants:
                        # নিজে লাইভে আছে কিনা পর্যবেক্ষণ
                        if isinstance(p.peer, PeerUser) and p.peer.user_id == me.id:
                            if not p.left:
                                is_still_in_call = True
                            continue
                        elif isinstance(p.peer, PeerChannel) and p.peer.channel_id == entity.id:
                            if not p.left:
                                is_still_in_call = True
                            continue

                        user_key = getattr(p, 'source', None) or (p.peer.user_id if isinstance(p.peer, PeerUser) else None)

                        # নতুন ইউজার মিউটেড অবস্থায় আসলে আনমিউট করা
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
                                print(f"🔊 ইউজার আনমিউট করা হয়েছে: {getattr(p.peer, 'user_id', p.peer)}")
                            except FloodWaitError as fwe:
                                await asyncio.sleep(fwe.seconds + 1)
                            except Exception:
                                pass

                    # কোনো কারণে হাইড বা ড্রপ হলে তাৎক্ষণিক রি-কানেক্ট
                    if not is_still_in_call:
                        print("⚠️ লাইভে ড্রপ লক্ষ্য করা গেছে! পুনরায় রি-জয়েন করা হচ্ছে...")
                        await join_live_call(call_input, active_peer)

                    await asyncio.sleep(2)

                except FloodWaitError as fe:
                    await asyncio.sleep(fe.seconds + 1)
                except Exception:
                    # লাইভ বন্ধ হয়ে গেলে বা হোস্ট কল কাটলে লুপ ব্রেক হবে
                    print("📴 লাইভ স্ট্রিম সমাপ্ত হয়েছে। পরবর্তী লাইভের জন্য অপেক্ষা করা হচ্ছে...\n")
                    break

        except KeyboardInterrupt:
            print("\n>> স্ক্রিপ্ট বন্ধ করা হয়েছে।")
            break
        except Exception as e:
            await asyncio.sleep(4)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
