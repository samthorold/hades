# Copyright 2023 Brit Group Services Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# https://github.com/ki-oss/hades/discussions/18

import asyncio
import logging
import os

from hades.core.event import Event, SimulationStarted
from hades.core.hades import Hades
from hades.core.process import NotificationResponse as Resp, Process

logger = logging.getLogger(__name__)


SECOND_CHAT = ["gaz", "baz"]
FLATMATE_SELECTION = "gaz"


class RoomAvailable(Event):
    pass


class ApplicationMade(Event):
    applicant_name: str


class SecondChatScheduled(Event):
    applicant_name: str


class FinalDecisionMade(Event):
    applicant_name: str


class Resident(Process):
    async def notify(self, event: Event) -> Resp:
        logger.info("Resident received %r", event)
        match event:
            case SimulationStarted():
                self.add_event(RoomAvailable(t=1))
                return Resp.ACK
            case ApplicationMade(t=t, applicant_name=applicant_name):
                if applicant_name in SECOND_CHAT:
                    self.add_event(SecondChatScheduled(t=t + 1, applicant_name=applicant_name))
                    if applicant_name == FLATMATE_SELECTION:
                        self.add_event(FinalDecisionMade(t=t + 2, applicant_name=applicant_name))
                    return Resp.ACK
                return Resp.ACK_BUT_IGNORED
            case _:
                return Resp.NO_ACK


class ProspectiveFlatmate(Process):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__()

    async def notify(self, event: Event) -> Resp:
        logger.info("%s received %r", self.name, event)
        match event:
            case RoomAvailable(t=t):
                self.add_event(ApplicationMade(t=t + 1, applicant_name=self.name))
                return Resp.ACK
            case _:
                return Resp.NO_ACK


hds = Hades(track_causing_events=True)
resident = Resident()
gaz = ProspectiveFlatmate(name="gaz")
baz = ProspectiveFlatmate(name="baz")
daz = ProspectiveFlatmate(name="daz")
hds.register_process(resident)
hds.register_process(gaz)
hds.register_process(baz)
hds.register_process(daz)

if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "DEBUG"))
    coro = hds.run()
    asyncio.run(coro)
    for key, value in hds.event_results.items():
        pass
