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

# ক্রেডেনশিয়াল ও সেশন টোকেন
API_ID = 32054831
API_HASH = "89fc23d0ff6763a53004996fe0c6cab2"
SESSION_STRING = "1BVtsOMMBu1WGKCnjA_joyvpHQy2oQ3Y9P0Ncgf8JM7OtAkvKxMTPljd1Sg-viJEMP9rPKZynCFNcI5tbaKL25zRHAneu4rcPCC89ninLD0GnYqY35MsFaT-beg9mIrJBiGqiBznlKs4RNwZHMesqMhryDEpNZRa48pzCUUihR05tcJr5L07ooNhPIOPjYC8sSWYa1SNpO68XgeCtbwoJ31EoQvEPP4FcSuDZoLZvaEasK_UV89hf-QZir-x1aPrtfjcmaY2VtutW8Wql5xK-QocrxmopEN4iY_5hxW43YNmC4BY-4p88FfBfQuPWZD3ivs-5Pd1nV5lKwhnRto1Ukp36FMcsrGc="
TARGET_CHANNEL = "DARK67HACK"

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def make_sdp():
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

async def join_live(call_input):
    me = await client.get_me()
    join_as = await client.get_input_entity(me)
    for _ in range(3):
        try:
            await client(JoinGroupCallRequest(
                call=call_input,
                join_as=join_as,
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
    print(f">> স্ট্রিং টোকেন দিয়ে লগইন সফল: {me.first_name} (ID: {me.id})")

    entity = await client.get_entity(TARGET_CHANNEL)
    channel_peer = await client.get_input_entity(entity)
    unmuted_users = set()

    while True:
        try:
            # ১. চ্যানেলের কল চেক করা
            full_chat = await client(GetFullChannelRequest(channel=channel_peer))
            call = full_chat.full_chat.call

            # ২. লাইভ না থাকলে চালু করা
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
                    print(">> লাইভ সফলভাবে শুরু হয়েছে!")
                except FloodWaitError as fe:
                    print(f">> টেলিগ্রাম রেট লিমিট: {fe.seconds} সেকেন্ড অপেক্ষা করতে হবে...")
                    await asyncio.sleep(fe.seconds + 2)
                    continue
                except Exception as e:
                    print(f">> লাইভ চালু করতে সমস্যা: {e}")
                    await asyncio.sleep(5)
                    continue

            call_input = InputGroupCall(id=call.id, access_hash=call.access_hash)

            # ৩. লাইভে স্থায়ীভাবে জয়েন করা
            print(">> লাইভে জয়েন করা হচ্ছে...")
            joined = await join_live(call_input)
            if joined:
                print(">> আইডি লাইভে দৃশ্যমান আছে এবং সক্রিয় রাখা হয়েছে।")

            # ৪. অডিয়েন্স আনমিউট এবং হার্টবিট পিং লুপ
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

                    for p in participants_data.participants:
                        if isinstance(p.peer, PeerUser) and p.peer.user_id == me.id:
                            continue

                        user_key = getattr(p, 'source', None) or (p.peer.user_id if isinstance(p.peer, PeerUser) else None)

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

                    await asyncio.sleep(3)

                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 2)
                except Exception:
                    print(">> পুনরায় লাইভে রি-কানেক্ট করা হচ্ছে...")
                    await join_live(call_input)
                    await asyncio.sleep(3)

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
            await asyncio.sleep(5)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
