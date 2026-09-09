import sys
import subprocess

# ১. প্রয়োজনীয় লাইব্রেরি অটো-ইনস্টলার
try:
    import telethon
except ImportError:
    print(">> Telethon ইনস্টল করা হচ্ছে...")
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
    GetGroupParticipantsRequest,
    EditGroupCallParticipantRequest
)
from telethon.tl.types import InputGroupCall, DataJSON, InputPeerUser, PeerUser, PeerChannel

# ক্রেডেনশিয়াল
API_ID = 32054831
API_HASH = "89fc23d0ff6763a53004996fe0c6cab2"
SESSION_STRING = "1BVtsOMMBu1WGKCnjA_joyvpHQy2oQ3Y9P0Ncgf8JM7OtAkvKxMTPljd1Sg-viJEMP9rPKZynCFNcI5tbaKL25zRHAneu4rcPCC89ninLD0GnYqY35MsFaT-beg9mIrJBiGqiBznlKs4RNwZHMesqMhryDEpNZRa48pzCUUihR05tcJr5L07ooNhPIOPjYC8sSWYa1SNpO68XgeCtbwoJ31EoQvEPP4FcSuDZoLZvaEasK_UV89hf-QZir-x1aPrtfjcmaY2VtutW8Wql5xK-QocrxmopEN4iY_5hxW43YNmC4BY-4p88FfBfQuPWZD3ivs-5Pd1nV5lKwhnRto1Ukp36FMcsrGc="
TARGET_CHANNEL = "Capsan_05"

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def make_sdp():
    """টেলিগ্রামের সক্রিয় অডিও সংযোগ পে-লোড (হাইড হওয়া প্রতিরোধক)"""
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

async def join_live(call_input, join_peer):
    """লাইভে হোস্ট/স্পিকার হিসেবে দ্রুত প্রবেশ"""
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
            await asyncio.sleep(0.5)
    return False

async def main():
    await client.start()
    me = await client.get_me()
    print(f">> অ্যাকাউন্টে সফলভাবে কানেক্ট হয়েছে: {me.first_name}")

    entity = await client.get_entity(TARGET_CHANNEL)
    channel_peer = await client.get_input_entity(entity)
    user_peer = await client.get_input_entity(me)

    print(f">> চ্যানেল [{TARGET_CHANNEL}] প্রতি সেকেন্ডে মনিটর করা হচ্ছে...")
    print(">> লাইভ অন হওয়ার সাথে সাথে আইডি জয়েন করে ফেলবে।\n")

    while True:
        try:
            # ১. প্রতি সেকেন্ডে চ্যানেলে লাইভ এসেছে কিনা চেক
            full_chat = await client(GetFullChannelRequest(channel=channel_peer))
            call = full_chat.full_chat.call

            # লাইভ না থাকলে ১ সেকেন্ড পর পুনরায় চেক
            if not call:
                await asyncio.sleep(1)
                continue

            print("⚡ লাইভ স্ট্রিম শুরু হয়েছে! তাৎক্ষণিক জয়েন করা হচ্ছে...")
            call_input = InputGroupCall(id=call.id, access_hash=call.access_hash)

            # ২. চ্যানেল হিসেবে জয়েনের চেষ্টা (হাইড হওয়া বন্ধ করতে), ব্যর্থ হলে পার্সোনাল ইউজার হিসেবে জয়েন
            active_peer = channel_peer
            joined = await join_live(call_input, channel_peer)
            if not joined:
                active_peer = user_peer
                joined = await join_live(call_input, user_peer)

            if joined:
                print("✅ লাইভে সফলভাবে জয়েন হয়েছে! মেম্বারদের আনমিউট করা শুরু হচ্ছে...")

            unmuted_users = set()

            # ৩. লাইভে থাকা এবং প্রতি সেকেন্ডে মেম্বার আনমিউট লুপ
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
                    is_in_live = False

                    for p in participants_data.participants:
                        # নিজে লাইভে আছে কিনা নিশ্চিত হওয়া
                        if isinstance(p.peer, PeerUser) and p.peer.user_id == me.id:
                            if not p.left: is_in_live = True
                            continue
                        elif isinstance(p.peer, PeerChannel) and p.peer.channel_id == entity.id:
                            if not p.left: is_in_live = True
                            continue

                        user_key = getattr(p, 'source', None) or (p.peer.user_id if isinstance(p.peer, PeerUser) else None)

                        # নতুন কোনো ইউজার মিউটেড পেলেই সাথে সাথে মাইক ওপেন করা
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
                                print(f"🔊 সাথে সাথে আনমিউট করা হয়েছে: ID {getattr(p.peer, 'user_id', p.peer)}")
                            except FloodWaitError as fwe:
                                await asyncio.sleep(fwe.seconds + 1)
                            except Exception:
                                pass

                    # যদি কোনো কারণে আইডি ড্রপ হয়, সাথে সাথে রি-জয়েন করা
                    if not is_in_live:
                        print("⚠️ লাইভে ড্রপ শনাক্ত হয়েছে, পুনরায় রি-জয়েন করা হচ্ছে...")
                        await join_live(call_input, active_peer)

                    await asyncio.sleep(1)

                except FloodWaitError as fe:
                    await asyncio.sleep(fe.seconds + 1)
                except Exception:
                    print("📴 লাইভ বন্ধ হয়ে গেছে। পুনরায় ১ সেকেন্ড পর পর চ্যানেল মনিটর করা হচ্ছে...\n")
                    break

        except FloodWaitError as fwe:
            # টেলিগ্রাম রেট-লিমিট দিলে প্রয়োজন অনুযায়ী অপেক্ষা করে আবার ১ সেকেন্ডের লুপে ফেরা
            await asyncio.sleep(fwe.seconds + 1)
        except Exception:
            await asyncio.sleep(1)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
