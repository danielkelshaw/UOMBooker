import uombooker
from uombooker import Location, Session
from uombooker.utils.exceptions import AlreadyBookedError, SessionExpiredError, UnknownBookingError


# note: make sure to set this
fp_config: str = 'user_config.yml'

sessions_to_book = [
    (Location.AGLC, Session.MonAM),
    (Location.AGLC, Session.WedAM),
    (Location.AGLC, Session.FriAM)
]


def err_msg(msg: str, loc: Location, sess: Session) -> None:
    print(f'{msg}: loc={loc.name}\tsess={sess.name}')


if __name__ == '__main__':

    for loc, sess in sessions_to_book:

        try:
            booker = uombooker.Booker(location=loc, session=sess, config_path=fp_config)
        except SessionExpiredError:
            err_msg('Session has expired', loc, sess)
            continue

        try:
            booker.book()
        except AlreadyBookedError:
            err_msg('Session already booked', loc, sess)
            continue
        except UnknownBookingError:
            err_msg('Unknown Error', loc, sess)
            continue

    print('Sessions Booked...')
