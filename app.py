import streamlit as st
import sqlite3, hashlib, io, math, re, unicodedata, json, os, base64, gzip, shutil, tempfile, urllib.request, urllib.error, urllib.parse, uuid, time, threading, functools
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB = "bar_inventory_v3.db"
ML_PER_OZ = 29.5735295625
DEFAULT_TOL_BEER = 1.0
DEFAULT_TOL_LIQUOR = 1.0
APP_VERSION = "0.6.0"

# V0.5.1 recovery floor: verified SQLite snapshot supplied by the Developer/Owner.
# It is only used when the runtime database is missing or clearly reset (no operational
# sessions/counts and no authorized-user roster). It never overwrites a healthy database.
RECOVERY_SNAPSHOT_SHA256 = "a6057e92fae6cea9e737eed41b1e1ccaddfe88d65816ac79cfd57542c480985e"
RECOVERY_SNAPSHOT_GZIP_B64 = """
H4sIAClUnGoC/+19C3wcVb3/mZ2d95mZpNlkm6RpJk3SNM2ju3k0TUrbpGmaPtKWtilvGqebabLtZifd3bRN8XE3CHLlqhcQX5frA0RUBEWubwSkeMW3oFxF
RFARBQVBfCB45Z7ZObNzkmxa6t+/H+VzvpTM9/c779957Dm/2Zndu3sonrGMg3ZqwswY7aAIMAzoNQwA2GsBAFXARyX6P0jIDDgtUB6tJ45wTmT9JUdR4V4o
KCgoKCgoKCgoKCgoKCj+fihTZfQXalcA/RGd0a7QbtLXavfp+/VPa0/oV+vH9EpqIwoKCgoKCgoKCgoKCoq/JZayfUzMTCXsdKuZmjDTrYk1Xb1jE2Y80Rqz
J6DBDqDgtJm2U5n4ibSZzMTNMduPoFSxG5hDZtJKxMxpe8rKZKxuP1SuYLuZxBTK4JB91Eq1dfhBUjnbxZjJsUTrqJmcjhBlitVsP5OMx+xEImXHxk3nn530
w4Vl7FbGOmolppOtKTttJTPjZqItEo34UfjFbCeTMJPmeDw90U3kzTkVmnCam0yZE3b6iB/E1rLbnaA4SjZhJzNWesxOnjAT1gk/TmA5uxvl6yRNmq0xxxoo
snU8jqjpRwsuY7dLSJOYzsRj6VEzY06m7ENWLJP246iO8Yvo+KOgoKCgoKCgoKCgoKCgeDXDuf+vqbuB/m39vfqEvk5XtIe0Y9pm7cNaqfq4ers6gwIpKCgo
KCgoKCgoKCgo5iPC11SG25m2SNvqlkh3S6R919kDO7fuHNzUt3XofF87HF3d0xHtiXZoZ5Yg0q2eYYIOODdBW8EEbU6CaFdPZ7tyZgnau+S5CaL9Q7v2FkgQ
ae9p6+6JrpbOJAFqRoc4L0HBKkVzjW5HCYQoSlDuJVjT0u4lOHdgYLuXwlEPt0VQk3ui7eyZpEBldHYHVuUqJc1LQVQqlwBVKtLWE2mf1QgnpGCro06rO1BH
dPFnkiDa09nGnVmCjjVB5/4/q38T6E/rj6ELBQUFBQUFBQUFBQUFBQXFPzqK2SCoLu0/eXssYyWsdNpMWEogCMLFQ/GYnbJPFDNBUFneb6WOWifMA3Ymk7Dk
3Pn/EaD/Xn9E/xU1IQUFBQUFBQUFBQUFBQXFPx1UtprJewNYiQ0zOUdAQGYrJewFUGUb9AtPBfSn9G/on9dv1N+in9AtfZf4n3qz9ivti9r7tDdoptarVat/
Vh9WP6u+U51Sz1O71RB8Af4Q3g0/BK+ER5Q07IJlygvK/eIu5RpxStmldCkVCis/Lt8p3yC/WfkvebcckYulJ6SvSbdJ75RsaUiKShXii+Kj4j1wr14kRsSQ
8BTtMgoKCgoKir8tVvRLgFkLKiUgBobHLSOdMVNpIz1ppg4n4mPGsXjS2mijnULCrNiIYla7MffErYMoZsYLq+pDYfVu2GY7lZlKWsYeO+0F19Wj4HYnWAr0
m5MZM540dtipMTNpbEIF4VjLG1CsLjfWcCo+mbCMvVbM2BEbnIonk1Y6jePVSihe1I23DRVi9E+hXYtt7I0njlopHKlyveDWKHB2PGlnjMFUfCxu48DydSiw
xgnsHzdTo3YyaU7joKVnoaAmJ2ivOXU0Ppa0k8bGhJmM4fDStSi83AnfYaUSdsbLscfL0S1upx33alLTLbjVRU0/YKWSVsbIZ+21fI3gdgJKffI209hmJsxJ
6+RttjFsHZmKJ0wcb3GX4HZBYFM8baZQvb0WhVejkCq3kNi4efImL0lFJwqozQWk7GNJ1CvTZgKHNXagsD4nbJs9nkzGLeNcM3HYSjkNjh02hlB1vahV7Shq
oxN1i5UcTcVjhxvSxmDca0B1GwpucYIHU9a0MWg73XKOPXrYq8aSKIrQ4EToO5C2E1OZWaHKBFjoldLhVV7DUGnGcGrKG1PlrZ7FN9oTB8xpojZ1LYI7kJAx
khnUgShoDDVrKH5kypry+qWq2WtSf8qaMI1RNJDMmOlZtLTJ6+i+SStle4aoXOmNq42JKWfopYg0ZY0osDIXaMYT1rQ3Ypes8Fo/mDKTo8YOM4Ws7VVE+Tjg
AVhqSG4c4AytEzEzYWxNWGP5zqpY7nXkFvOomTSN/sTUARymK4ADlRHJNQjKIGdc0lr1dSiws+AMPHc8np/HS2q9iuIqXGBOmhmvm6qXeb2MQzch2+5xXjfm
1bHGqyOOcE58ND8QN/jLB551+UkHwOJqb2T3m2nT6Dsx5bW7fKnXz0N22uhD9hvzzL24yku0xUqlzFHUF17IEi8kuiYSMfrtmJdmSaXXwlzIHmvSTpujXmhF
hdeAXGhu4nthteWCa8LAHiuNFhzTGDieSaG6nrzNOuRFqlrsDSrHNtumEnHbiHZ3tHmjJ+yNHj+4K4IDjTIUuCq3CpgZNLmN/lQcLbKJeH6WV5d6HeAnn1XH
mpC31vgR5jSxumR+HrOaULPIX6/S5kR8DJl9bh7FXh5+lFn1qC6aH2FWIUt0rxtwW2eFLtW8RRiHzil/iTon9aylvxmi0EF3WfM/HYbRAInH4mjUJYyzE/6g
Xqp4ZblDZa7N0RrEgYrehQdvjSy5bZ3zcTRoJ0ZxlJAoAMlZS3bYiXR+tpQISBtG2n7bTnlLRTGPlCVIuTe/5JRxSOUsgQPpSSsWz68IJUGcfqc1lh/5RSxS
FiPleed5xgogTWOuGGQq09g7lTyQso55VWNw1dxQrHXu//eLzwF1g6rqnFonP6K8TrlZuUpZLj0rDynrYRiugV/R4tp2rUnaLw1Kb9Mz+tP6/YopH5A71RPq
OzRV/bb6tP4uqUUpUu6W71L+It8A/yBfoi/Te7Ufwh9L98Ip+DF4DbxAf41+q/Ym9RPa9dpd0pT0A7lIPU8qk27S3yQ+pzwsv6B/ie7SKCgoKCgoKP4/oI5D
x2/m1A6Q/jIObQGZub6PjeUc2tEzBdwefW6CuRvG3sLqDW4+BdwV68NcjZ/AT7FuCYc2rkxhR8VZJRza1jGzvBRr3YzmuSh6qrmoU8BC/olu1zyndk6scZs1
1zPRVcpV5fKe5ZZYvZirdbTzfBKdDVwfCjitQ6KjkkN7WqagN6K9ikP7cWYBV0RbBYeODkwhP0TUtc+803PEbcMcD8QqN/Y890PrMq4r1+KFfQ8tbu0LOh6a
3Y6b5XVocsdGAZfDyhBX6YTM8jc0uk0s5GxY4VbuVP61Brdv5rsZlhtce65hC3nw6mu4zvkRSAdDnVuzQt6FWrfXFnAtLHMrNd+vUDMrx1kuEwNPtDkehWq3
3+a5E5a60ef6Eqpc9TxHgltuIS9CpVvX+S6ECtc+p/AflLsDo6DzYLE7CAp4DsJLuVXO/FzAbVDmWnYBn0GpO/kXdBiE5qaeVeESb+lYwFWwyE29gJ+geG7o
rLyLXBMX8hDo7tJX2D2gzUo3yzegruQGc8vL6R0D0C2isFdAcSu+wHlfdo2yoHNawmsz6Q0QF3FhxxSEL0Ao4kqc9T2/DPDuOjTHD8C5KUkvQFDnipEq7wNg
8XpTyAMQWMTNO/87z/8H9KeB/gL6Q0FBQUFBQUFBQUFBQUFB8c8PKcCC8o32qDVm8gwLSjaaKTl3/n8G6H9CfygoKCgoKCgoKCgoKCgoKF4FkNlyxj3/B3i2
RELnf1W7G2jwIaB/Xb9WH9H26Y3a89qV2lL1F+pt6iXqgKrDhyR59n/UjhQUFBQUFBQUFBQU/1Do0GRQU8m0S2oYzPupPKXAD/HlfiKtQz2jVJFuNxU8s1S4
LKVAKu+n9rgCv8vnppLPKFV7Vy5Vp5RPNf9H9wIFfqEvl0roFM8gmfM7fW6yjmA+mTTvp+gCBX6GLpesXZC8VPN+5i9Y4Cf+colQT7ef6cjgz6B2zs/wuXbn
zqhNnW1uKtZrU/m8XwkMFPgRQve3BjsCrzhV7ocI3VTtzBz7EanYAr9GmKsghwzC6C86dqlyLxQUFBQUFBQUFBQUFBQUFK8qLMle5Dz/D4qoKSgoKCgoKCgo
KCgoKCgoXs1wzv+M/hxA/ygoKCgoKCgoKCgoKCgoKF41B34mCKqlHWZqzEzFM7nf/2P05wH6R0FBQUFBQUFBQUFBQUFB8eoBZInzv/v7f48B/Vn0h4KCgoKC
goKCgoKCgoKC4p8SWoADEiM0bMCne43JydKGF1zZ/f2/54H+Iv0GAAUFBQUFBQUFBQUFBQXFqwh8UGKYhgCHLpJE3/9HQUFBQUFBQUFBQUFBQfHqh3P+5/Wt
QH9Sf1C/S79RTyKBgoKCgoKCgoKCgoKCgoKiMGp5drs+asYT0yPx5FErmbFT0yOj1kFzKpFJj6Qta9QajXZy7Pb2yZQ9OhXLxO0kETOdMVMZa3TEzLRF2la3
RNa0tEeHI9GeaFtPZM3iINupp8ctKzMyHk+78d0MQyzbomfshJUykzFrJBE/MmWnoosCbCOhPWBZqWgpw7YUp82DVsYpzI4dHpmMZaKdcu78HwN6TH+T/mv9
Zv0h/V7amRQUFBQUFBQUFBQUFBQUZ+4ZYLczp3EM8E6c0/gFuMVsJ1PICRAMsS3MXB8Au4htZGa7AAIlbIs01wPg/v7fRQD9o6CgoKCgoKCgoKCgoKCg+CuQ
rWEEsIrJHmvfuvOcgZ3DfXu27jI2bXUugc3xhJk24sl4LG4mrLQxaiWM0ZO3mEZb1IjZyUzcSlpJw/UDmKm4vQpdU+YoSjNppWwjaRuxuJVKWSjyxGTCythr
nWRpK3XUjWSmTCNlHY2n4ydvTxoTZnLKTLTmv1oQGY529bR39bRF1EAtkMGNQPuBdkPwGi2lieqD4Eblj3K/dKd0pXhSfLtgC0X8o3wTa/BAf1AfQwn+3pi5
RBbC0ShzWU3GPJCwCO+IlU7HUbPna5T+PQN9wwPGcN/GoQFjfvgK2cghPmps3Tk8MDiwxzh7z9YdfXvON7YPnN9s4Hgjo2bGMoYHzhs2du5C/+8bGvLDMtOT
c8NwrlOoI0b8rJuNWMoyXTfOvMymDkzEMygsX49NA5v79g0NG9Fm1M0ZNDacFM1EG2LTsQQu2IvbsKlv69D5Dc2o4+MpVI49aSXjyTGvuWRdcBU379ozsHVw
p9PaFbi6jcaegc0DewZ29g/szTUhvQIpG3kQmKSTmeLvNtsP8UK4qoq5rCE327FbNO1dhVkz29Oebj7H0PQbcyYPEcGfhElzYoGZfMDOZBLWyEQCzY2+IWd+
xQ6bYxYx9/NTcCOarImEiSahGcvEj1qFJvRUMp4ZidnpDM5ujl94XpKIV499O7fu3jewwqloc75OzWRtGptnzWmiwbPmNdbHLXdy62PsnXTIUVD8U+4wA6oQ
rq5msntzS2XMjh3OoBUlnSfarMUyr16x0DLpL4TugkOskQstao2XRmGuEpdHc5WYsI9aE2g5S+eJOqsSefXplmwvYsE9WD5w4U0Y/mgovOIfyUyPHDDTVm4d
JvQHU/bESMJGq2ThbVPGLhg6f8eXnpqcTKAtOt69payDVspKxty6ernZB3I7dic3HG/hjWKuxu7Kbx2Zih91P0EK7Ob8ds9a+POflM6yf+mFihBuaWEuj8/Z
UcfsKdQ1c2W4wG7aDX2le+mCHXGqXsL5FjD4K+jJSef4Y0+lR1CEWbY6is5Tzk1R/BE8vw9esaX9hs2ydIHTBorxV3bV7E91whSzUnh6t3ejEh8eqGZAPDlq
HU8fScQz1og5lbFzcn78pkeieSqPi+5CUp0bD3l9nkizRgBZ3BkuJI2rBD7cX7VQ5bymj0Q9JrZzfHiwZqEE/n5mJOpzPguDQrimhsnG3JUxH+Izbvba6O+L
TjOcT7FG5ubDiLPJmz17G9Fa/e5/yE8QFSYAVM4Byl36B/SdyjnaE+rz6nXqFjUIP6ddBmvpZywFBQUFBQUFBQXF6TAWlEG5urtJam8X+5Kj6EyfMFPmhJ00
W2NmMhN3jhDH44iavWMTZjzRGrMnBgd2DuzpGxrZ0bezD5053Ht13S2R6HB0dU9HO/pHPBkc7ehpj/R0th9gZNCobg+jgqRNZsY0+pJmYjoTj6VNj4wiNTpL
HbLQWcovrW/Tjq0782W0O2V0dqE8C9wiHIQSqFf7whJo7zdTCTtt9KUmTHSQcnir6fDWxJouP++9w32bN5OVXd0Tae+JRLVNYMffzMRbZQk0qRucWm0zk1bC
6Den7Skrk7EOOWLMk7pPXa8oavZGSQK1areT1dBUzEwb2+yjVirh0EMOa+s4XR7t7XtECQyoXU4efckxVJ1NZjJuJUxjjzkaT6Dr2Sc/krJOmMmxROuomZyO
nMZeqHPX7BMksEHtd/LcGY/ZCSfTaTNp7LFj46bRP27G7GQyF5ByNLGc4nTZdkR38RJoUbc62Q4ctRLTToZpK5kZNxNWTm5NeXJbJBo5XYZtEdQbff9PfTmi
OKN4wBnF4l5nfphjNurPtDPI0B87lYmfSGN9wep4Q7jDeWB+Tg3beqJdBzkZDKqduQKGrIxz092ZKeMnbzH2WubJ26wTxg5rFE3LBJo24/H0RHfXQuW0OZmi
qdEZJcvp7Ons7omu3s068747V84OZ34kJ3J/nbmfPrJwlm1tyIw9kW7y2f+OnsgaNOkvDsigUt1e6czwHTnPlTmBL3YyY6XH7OQJ1HEn/MznLiBtw2j2taHq
dcx+tYAzGLqc5/+hrgH9G/o5uqY/o1+rt+kf1TfrP9W/rx/Tq+laTkFBQUFBQUFBQUFBQfHqQxFbz5A+Lug8RT/bI6GUsE3MHI+TrLO1DOE6kgx2gDmVG0is
YjcwC/p0BOeB/rmuGb6GHWRO6bvgZLaccb2NQYe6DghWYSsZ7DgIFLONc9yEufO/dgXQH9EZ7QrtJn2tdp++Xz+mPaF/Tn+vXknHBAUFBQUFBQUFBQUFBcXf
EkvZPmbhb5RA50B9qu8CKM6BesEvfsgVbDdT+PscUjnbxRT8VoZYzfYzp/h6hbCM3cqc+gsTvPPKvkJfKeCWs7uZ038lKOjUu/A3CFjnjYGn+SJAYBm7XTrN
94Cc9/9pwh1A/6bOaf+j3qbuUWvghPyi/G35g/JqqVtMokAKCgoKCgqKfxhkVy0Rwhe2MNlY7lHI+Ohx500S+KHc/KtfvGdMvWc25z69W4kfg9y6c9PAecYr
zMTYtXP+Y8D+47DN/oOtzeQjq9ktlUL44igzo8+qsfeYbO5J79wT3e47bkbw09DzH6gNFqz06fKZXev8w7nku36ayZf7NM95506z/3R2Y/ZEhRCurWUuXeu+
pcROjxwwM7FxK01Qdva7SvyA0z4yjXZyhd895ASMpeypyVf45iHnFUKne7b8jF8JlCgXwk1hJlub78Zc2IjlbCtzNIBbjh+R9fuJiOh0h5tnTmw0zt2CijLc
sK17/adnF/PhdeGFHgB2M2zLXcobw6ePGs1dFs9MlgnhcJi5bEOuA3PK3J/wrE5bltMt8zrMw1/xcPBkPDkybqbHZxvff39MQzNuOpG8eU6xKTsxZ0gY/VsG
+revyAVs3WmsaMh9t7ihuQF/DRixOU8WIE3u2/8NjY2neFXNnIITZtqZ/WOoDXj4zBtPzksOJtH5bMSMxdAkmv8um8ZsNJSbMzON7lPm1pgZmx5J2cfSBC2d
/aS5H3DaOWNPpWLWSO4V6bhCWIVS+xMiZR4byVjHM7NexBCfcGpeYG40rio51ePqaXTSjCfH0KDyWOjiRbm3F2XVXBs9tXctmdU6T7visDXtljurRUfNxNSc
7m6cWVace1L/jSX5dcdZE9J5smjempNT/9UrjvfSkFmryvy3NniWzOVT4KUcxpEp55iL38VA6O0TI5Norck9NE++aGHeSvbKX5bR2FLEh/sqF+q0lBWLTzrv
C8CkODugC+HKSmbGzNkUq/GlaJY9sfK0r5uab7Qze+cFssqR+bbCb4Eicic+aRsbo9qp3vuQf/vLSDRPdRkApjN4JdD/pD+nP6n/RH9Iv1//mn6P/nn9k/pH
9ev19+hX62/WZ/RpfVIf0/fr+/QhvV/v0aP6Cr1aL9NVPai9pP1We1J7TPu+9i3ty9od2u3aR7UPaO/S3qZdrr1Oy2iHtQPa+drZ2qC2XuvUmrVarUIr1kT1
ZfUP6tPq4+rD6gPqV9W71c+ot6o3qtep16hvVrPqcdVWD6oXq/vUIbVf7VGj6gq1Wi1TVTUIX4K/hb+EP4bfg1+H98DPwU/Am+B74dvhlXAGHoc2PAgvhsNw
O9wI18BWWAcrYDEUlZeV3yu/Vn6m/FC5X7lPuUv5tHKLcoPyHuUq5QrlDcpRZUIZVS5QdiuDynqlQ2lSapTFiq7w8p/l38pPyo/KD8pfl78kf0a+Rb5Bfrf8
Nvky+RL5iDwmXywPy9vkXnm13CwvkxfLmhyUXpSelZ6QfiQ9IN0n3SV9SrpZ+oD0Tukt0qXStGRLlnShtFsalNZJ7dJKyZDKJCgFxBfEZ8THxR+K3xH/W7xD
/KT4YfG94pViVtwlxsRj4vni28UJsUGMilXiWnFALBEl4Q/Cr4XPC98SfircK7ws/EC4WrhOuEL4kPAJ4fVCRjCFc4V6oVvYIawSDgn9/P8KAv+8UCxU8k/y
j/Lf4O/h/53/IP9Z/j38g/yt/Dif4vfzr+Uv54f5bXwX38K9xOt8Lc/xvXw5913uEe6r3C+457i7uE9x13Pv4g5yJ7i3cpPczdwbufXcFq6D28NdxK3kDE7l
2OD9wZ8H/xR8mCsL/ib4keDtwfcFvxj8SvBaNNQoKApB4hhGCmgRphOzBqYDM4Npx0xi2jCTmShmdUwEs3pmFWYs04oZz7RgFmSaMROZJsw4ZiVmAaZR5BgJ
MWYFVglMg8vUCLMcswamHjODqcNMYmoxk5llmNUxNZjVMwZmLFONGc8sxSzIVGEmMksw45hKzAJMhVsplSnHKoFZ7DIYYcKYNTBlmBlMKWYSE8JMZkowq2MW
YVbPFGPGMkWY8YyOWZDRMBMZFTOOgZgFGMWtFGRkrBKQmGNKhBExa2AEzAyGx0xiOMxkJohZHcNiVs8EMGPRX5fxDB4YShC8jJkI/oIZB/4XswD4s1spBbyE
VQJ40WVyBPwJswbwAmYG+CNmEvgDZjL4PWZ14HeY1YPnMWPBbzHjwXOYBcGzmIngN5hx4BnMAuBpt1Iy+DVWCeBXLpMi4CnMGsCTmBngl5hJ4BeYyeAJzOrA
zzGrB49jxoKfYcaDn2IWBD/BTASPYcaBRzELgB+7lZLAI1glgB+5TIyAhzFrAD/EzAAPYSaBH2Amg+9jVgf+B7N68CBmLPgeZjz4LmZB8ABmIrgfMw58B7MA
+LZbKRF8C6sE8E2XCRHwDcwawNcxqwf/jVkd+ApmBvgaZjK4DzMJfBUzEdyDmQDuxIwH92LGgS9hFgQnMWPBlzELgLvd6gngLlfFR8AXMWsAd2BWDz6DWR34
LGYG+AJmMvgcZhL4PGYiuB0zAXwcMx58CjMOfBKzIPgvzFjwacwC4Da3Ujz4hKviIuBWzBrALZjVgw9jVgc+gpkBPoaZDD6KmQRuxkwEH8RMAO/HjAcfwowD
N2AWBDdixoKbMAuA691KceADrioYAe/DrAG8F7N68G7M6sB7MDPAf2Img//ATALXYSaCazETwFWY8eCdmHHg7ZgFwTswY8G7MAuAa9xKBcHVrortB2/FbCP4
N9FhDNuXxqQ3jsmGcRxpPbgCq9YdwqqzwFuwau0bsKoH/CtWdY9g1RrwZqzqmsBk9Wsw6Uxg0nECk/bjmLQdxSR6Ac4oAv4dq1ZlMGndj0mLiUnzYUyaLsRk
5cWYNF6EyYopnGMDeBtWLT+GSf0BTOpiOFItuBSzZeBfMKsBM5gZIIsTVI9isvT1mFRNY7LkXEwqz8ek4hycvhxciVWLk5iEbRxWBi7DqtIjmIRSmJRMYrJo
DJPig5gUWTi9Dt6ImQYux0wFb8LR4OswUc7DRL4EE+m1mIh7MBF2YsIPY8LtxiS4FxN2HyaBswVnrDHsLlcRWD+IybqVmJy1HZO16zHp2YJJdw0ma7Zi0tWC
yeplmHQ2Y9LRjUl7FyZtnZhEl2AS2YHJqnZMWg1MWmoxaW7CpKkKk5XVmDQuxWRFByYNQ5gsX41JfR0mdfWY1G7EZNkGTGr6MDF6MalejsnSdZhUrcFkSTkm
lZWYVCzGpHwbJotbMQmvwqRsEyalUUxCbZiURDBZ1IhJ8QpMihow0fsx0QYwUTdjAs/CRKnARO7BRFqLiRjCRCjChC/DhCvBJFiKCRvGJLDIHSyBYoGTkCKi
u9cGzb3WS+61TnavhupeZcW9StC9ihzvXCXBFXl85YLuNci7V1Z0rwEWRXeKde7//4i5F+i/1X+ufx+d/O/Qb9Xfj878l+nH9cPovL9b36R3obN+ha5o/6s9
oz2qfUf7Ejrh36i9Q7tCS2kXaZu1CDrPQ3SWf0y9X/0COsG/E53eD6OT+yA6s9eqKnwZPgcfhl+GH4fvh2+GGWjBXbAbNsFSyCt/VH6ifFf5svJx5d3KpcqU
MoLO32uVZqVMAfJT8vfkL6Pz9kfl6+S3yv8ip+RR+Rx5i9yDztlL5SI5IP0OnbF/IH1NukO6VXq/dLX0RumoNC5dIA1J66WItEwKSTw6VT8l/kj8lni3eJt4
g3it+CZxWjwsXoxO1X1iu1gvhtE5+kXhV8KPhG8KdwofF94vXCXMCGlhVNgnDAirhWqhSGD45/if8g/wJ/nb+Rv4a/hL+QS/j9/Mr+INvogH3LPcT7j7uXu4
T6KT8dXcDHeYG+YGuFaumtODL6MT8GPB7wS/FLwt+IHgVcFs8FBwb3BTsCW4NKixf2GfZh9hv87ewd7Mvof9V/Y4a7Lb2LVsHVsaeDzwvcC9gU8Fbgy8I3B5
4GjgYODcwGAgEqgJyMxLzOPM91DHIajZi2TgjKbcKUpYqWYvzMkiEhkxwoWyF+RlQWzoXeSet2D2/LxaFI1Q9jwiltQre7HOJWLJoew5RKy6DS+4sdTsPqLI
+gDMDudkyQkUWTW716+hyDep2T2EHJTV7G5CFlmYPTufHRA5NbuLCA6UwuxOJEtY3q9mdxDBTvuH3NSiqDJChGvNbseytIsRGsbNA3HT6HRe7e68rz1txKyU
+9MaVtKImYdMDma35TMQBWSZrXlREKTeYs8yW4hYyDKDRKy8ZULZzYS6vjfgqrXsgFtnRlSBwIbDWnYToeCbmrRsP6EIQqhlNxIKMRiE2b581kDg9GwvDmeQ
GCgte1nNbnDtlEsxNqZl1xM5CCuRpdb53cZHkKHPIuQGVMJav/N5ZIgev/N5whDdRCxkiDVELMIQXYQ6bwg1u9rvPJ4Nq9lOQnaGSgchB6GabSdkEVWxzR8q
PGpBlAgOlMFsxB8q/JiaXUUEO0Ol1W8w5xighZAdAzT7TeOQAZr8NnCEAVYSsZABGolYhAFWEGrCAA1+lTjHAMsJ2TFAPSE7BqgjZMcAtb4BONSCZUSwY4Aa
3wAcMoBBBDsGqPYbHHQMsJSQHQNU+U0LIgMs8dsQJAxQScRCBqggYhEGKCfUhAEW+1UKOgYIE7JjgDJCdgxQSsiOAUK+AYKoBSVEsGOARb4BgsgAxUSwsBJm
i7zUqshGYFYnxIZQVsuLAtvfW++1VyVinaVmYV5k2I0KzCpEcDnMyoS4BmYlQuyBWZEQ18OsQIgqzPKEqMEsR4iobUFC1GGWJcRamA0QYg3MMoRowCwgxGXw
DYS0Fr6ekJbC1xEShK8lJAleQkgyPEFIHXCakKrgcUJqh8cIaTk8SkhtcIqQVsAMIa1S04Sp+yBMEYEheISQSuEkIZVAm5DCMElIi+EEIXXBBCF1wsOE1AwP
EdI6GCekXjhOSBvgGCEtggcJqRhahFQERwmpGsYIqQ4eIKR6aBJSC3wNIa2GI4TUDfcTUiu8mJBWwosIqRFeSEhN8AJCisLzCakSnkdICjyXkJbAcwipAuZ3
AypgWThMSDzcS0hBuIeQRLibkDh4NiEFlF25aexKcCcRJKg7/DERQPudIX/OBhp6S/Hqs53QnuVtb0LbCG15bwnWbiW0azY8hheqLUQxPXxokIi0vrcBLw2b
81opoIYGiDjahu/gOJuIOGWhfiKOvuGXuAobCW1tXttHaGs2/Bnn1+sbP2DADUTuy0LriRRre/ELvdV1RFOWBtSzCBHyobVEGskzIOwhSpFD3UScjg2/w/Vb
Q2ir8rvDLiL79kBoNRFpeb5pnYS2LW/zDiLpCjbUTkRa1YsfTw61EdpQvi5RQlvq1QVGCOuUwFWEFA61EikWe1WALUScrlAzEacz/9HWRGib8/2ykrDYulAj
EWeRl3toBaEtzpfZQJRZFFpOxKnOG6ye0NZ5Zap1hMHq2VAtEaklX+gyQrs6PyxriOp2hwwiTmu+0GpCu9L7CA8tJbSN+VKqCG1TXruE0EbzpqokGlypVhCN
UHhYTgQugYsJqULNbxZUEGAXq2WEiPYOpYSItg4hQkQ7hxJ/FQlw6iIiMBCGxd62AYlptYgIFFYqaJcgYVNFFM0XGhTVFwwF+oKkKL4gK7Iv1CmSL9RDMSfk
SkKfTIIv8U2Q9yV0IuB8SQwqwXwmgIOsHxQIK2gfIOGmpCHjB6H9H7L9+eLrgP6c/hP9Af0e/ZP69fo1+qV6Qr9Y34xO/oZepL2s/Ub7sfZt7U7tFu06bQad
+i/UhrRObbmmqy+rz6g/Vr+p3qneol6nXqkeUU11m7pWrVNL4V/gM/AR+Cl4FZyBk3A/3AGroa48q9yn3KZcj077aeWA0oNO+oL8e/ln8gPyB+W3y1PyDnm1
3CCL0gvSL6S7pP+Q/k06gc7050qNUrn4oviA+AXxY+JbUJUpKCgoKCgo/hmhznT6jlotwi2Zwbt9UVAFreEuvC/Ne5lm2n2Hq2aEZtp8z6qWd1jXz+B9v8is
ZTRZHEgaCTPn1zUOJMxkzDTS41bioLhkJkIUVucV5p0e1JlVRN3qA00z7uEA/TcINLa4aIs5bUS7fC+ylTSshHEwFR8dswxtpsX3tGp8U5M+0+w7Z7WgJL+s
zzQRGjHAvgxnVvr+XI2rmWn0IkSBFoiWLnGKnErixpgHzEN2/cyK3C41wDDdQAPX7O/MVStC1CsXT5tpIOrjeH5nlvvNUx3T1/vWUAuYvs43vYpMX+ubXiVM
v8w3vXoq09cQhRUwvUHUzTF9tW969fSmX+o3Vc2Zvso3tOqafgmhcU1f6ZteRaav8E2vLmT6ct/06qlMv5ioT870Yb950DF9mW8NWMD0pb7pITJ9yDc9JExf
4psensr0i4jCCpi+mKibY/oi3/Tw9KbX/abCnOk139DQNb1KaFzTQ9/0EJle8U0PFzK97Jsensr0ElGfnOlFv3lKhAvNCL4xFf/O2Azvm1xBJueIWP6dsZkg
EUsOzbBELP/O2EyAKLI+EJ5hPItWA4UtDW1xbkcljbaoNgP82iq5O0BvIBRBWdayrycUIsvC7Ot82ymcln0tER4oLVWzl/g3gJT9+7XsCSJC7gbQtF872blV
eNxvhEzcKjzmN1U2QtmjRCziVuEUEUsOZTNELOJWYZooEhkkm/INIs8ySPaIX1s5Z5BJQpEziE0ocgZJ+gaRkUEmiPCcQRK+QWTHIIeJCDmDHPLvf0iOQeL+
PQuJMMi4f8NDQgYZI2IRBjlIxEIGsYhYhEFGiSKde6cx/96pxKrZA8TdXed2iEnIzr3T1xCyc+90xL8dInFqdj8R7Nw7vdi/HSLt/z+7ThqnANABAA==
"""
RECOVERY_REQUIRED_TABLES = {
    "users","categories","products","locations","inventory_sessions","inventory_counts",
    "movements","cocktails","recipes","pos_sales","settings"
}
AUTO_RECOVERY_APPLIED = False

st.set_page_config(page_title="Inventario La Ramona", page_icon="❤️", layout="wide", initial_sidebar_state="expanded")

LOGO_PATH = "assets/la_ramona_logo.webp"

st.markdown("""
<style>
:root{
  --ramona-orange:#ff6a00;
  --ramona-orange-soft:rgba(255,106,0,.12);
  --ramona-red:#d9272e;
  --panel:#171c22;
  --panel-2:#1d232b;
  --line:rgba(255,255,255,.10);
  --muted:#9ea7b3;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"]{
  background:#0d1117;
}
.block-container{padding-top:4.4rem;padding-bottom:3rem;max-width:1450px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#10151b 0%,#0b1015 100%);border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container{padding-top:1rem}
[data-testid="stSidebar"] img{max-width:185px;margin:0 auto .3rem auto;display:block}
[data-testid="stSidebar"] hr{border-color:var(--line)}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:.48rem .62rem;border-radius:9px;margin:.12rem 0}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:var(--ramona-orange-soft);border:1px solid rgba(255,106,0,.20)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#ff7a18;font-weight:700}
div[data-testid="stMetric"]{background:linear-gradient(180deg,var(--panel-2),var(--panel));border:1px solid var(--line);padding:15px 16px;border-radius:12px;box-shadow:0 5px 18px rgba(0,0,0,.14)}
div[data-testid="stMetric"] label{color:#c5ccd5!important}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{font-weight:800}
.stButton>button[kind="primary"], .stDownloadButton>button{background:linear-gradient(90deg,#e74b4d,#ef6a4c);border:0;border-radius:10px;font-weight:700}
.stButton>button{border-radius:9px}
[data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stTable"]{border-radius:11px;overflow:hidden}
[data-testid="stExpander"]{border:1px solid var(--line);background:rgba(255,255,255,.015)}
[data-baseweb="tab-list"]{gap:.25rem}
[data-baseweb="tab"]{border-radius:8px 8px 0 0}
[data-baseweb="tab"][aria-selected="true"]{color:#ff7a18}
.ramona-page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin:.35rem 0 1.2rem 0;position:relative;z-index:1}
.ramona-page-title{font-size:2rem;font-weight:800;line-height:1.15;margin:0;color:#f7f8fa}
.ramona-page-subtitle{margin-top:.35rem;color:var(--muted);font-size:.95rem}
.ramona-badge{display:inline-block;padding:.22rem .55rem;border-radius:999px;background:var(--ramona-orange-soft);color:#ff7a18;border:1px solid rgba(255,106,0,.25);font-size:.76rem;font-weight:700}
.ramona-section{font-size:1.18rem;font-weight:750;margin:1.2rem 0 .6rem}
.ramona-note{color:var(--muted);font-size:.88rem}
.ramona-login-wrap{max-width:720px;margin:5vh auto 0 auto;text-align:center}
.ramona-login-wrap img{max-width:320px;width:72%;margin:0 auto 1rem auto}
.small-note{font-size:.86rem;opacity:.75}
@media (max-width: 700px){
  .block-container{padding-left:.7rem;padding-right:.7rem;padding-top:3.8rem}
  div[data-testid="stHorizontalBlock"]{gap:.35rem}
  .ramona-page-title{font-size:1.55rem}
}
</style>
""", unsafe_allow_html=True)

try:
    st.logo(LOGO_PATH, size="large", icon_image=LOGO_PATH)
except Exception:
    pass

def page_header(title, subtitle="", badge=None):
    badge = badge or f"V{APP_VERSION}"
    st.markdown(f"""
    <div class="ramona-page-header">
      <div>
        <div class="ramona-page-title">{title}</div>
        <div class="ramona-page-subtitle">{subtitle}</div>
      </div>
      <div class="ramona-badge">{badge}</div>
    </div>
    """, unsafe_allow_html=True)


# --------------------------- time zone ---------------------------
# La base guarda timestamps en UTC. La interfaz siempre los presenta en hora local
# de Ontario usando la zona IANA, que maneja automáticamente EST/EDT.
APP_TZ = ZoneInfo("America/Toronto")

def local_now():
    return datetime.now(APP_TZ)

def local_today():
    return local_now().date()

def now_iso():
    # UTC naive por compatibilidad con los registros históricos ya existentes.
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")

def to_local_datetime(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(APP_TZ)
    except Exception:
        return None

def format_local_time(value, fmt="%I:%M %p"):
    dt = to_local_datetime(value)
    return dt.strftime(fmt) if dt else (str(value) if value else "—")

def format_local_datetime(value, fmt="%m-%d %I:%M %p"):
    return format_local_time(value, fmt)

def operation_confirmation(action, business_date=None, detail="", event_ts=None):
    """Build a clear, user-specific confirmation message for successful writes."""
    actor=(str(user.get('name') or '').strip() if 'user' in globals() else '') or (str(user.get('email') or '').strip() if 'user' in globals() else '') or 'Usuario'
    ts=event_ts or now_iso()
    local_dt=to_local_datetime(ts) or local_now()
    registered=f"{local_dt.strftime('%d/%m/%Y')} · {local_dt.strftime('%I:%M:%S %p')}"
    parts=[f"✅ **{actor}** · {action}.", f"Registrado: **{registered}**"]
    if business_date is not None:
        bd=business_date.isoformat() if hasattr(business_date,'isoformat') else str(business_date)
        try:
            bd_txt=datetime.fromisoformat(bd).strftime('%d/%m/%Y')
        except Exception:
            bd_txt=bd
        parts.append(f"Fecha operativa: **{bd_txt}**")
    if detail:
        parts.append(str(detail))
    return "  \n".join(parts)

# ---------------------- Supabase Storage backup + safe synchronization ----------------------
# V0.5.7 persistence model (MVP-safe):
# - SQLite remains the transactional working database of the running Streamlit process.
# - Supabase Storage is the durable recovery layer.
# - Authoritative backups are IMMUTABLE unique revision objects under revisions_v2/.
# - Recovery discovers the newest safe revision by Storage LIST metadata; it does not depend on a
#   mutable manifest, latest file, or alternating slot. Supabase explicitly recommends new object
#   paths instead of overwriting when freshness matters because CDN propagation can serve stale data.
# - Legacy latest/manifest.json, slot_a/slot_b, daily and weekly objects remain readable only as a
#   migration/recovery fallback. Once a V2 revision exists, they are never authoritative again.
# - Every business write is committed locally, snapshotted with SQLite's backup API, uploaded to a
#   unique remote path, downloaded again for SHA-256 verification, and only then marked synchronized.
# - If remote and local changed independently, neither side is overwritten automatically.
SYNC_PREFLIGHT_STATUS={"status":"not_checked","message":"","remote_health":None,"local_health":None}
SYNC_LEGACY_MANIFEST_PATH='latest/manifest.json'
SYNC_LATEST_PATH='latest/bar_inventory_v3.db'
SYNC_V2_PREFIX='revisions_v2'
SYNC_HTTP_RETRIES=5

@st.cache_resource(show_spinner=False)
def _shared_write_lock():
    # One lock shared by all Streamlit sessions in this Python process.
    return threading.RLock()

WRITE_SYNC_LOCK=_shared_write_lock()


def _serialized_durable_write(fn):
    """Serialize write+backup workflows across Streamlit session threads in this process."""
    @functools.wraps(fn)
    def wrapped(*args,**kwargs):
        with WRITE_SYNC_LOCK:
            return fn(*args,**kwargs)
    return wrapped


def _supabase_cfg():
    try:
        sec=st.secrets.get("supabase_backup", {})
        return {
            "enabled": bool(sec.get("enabled", False)),
            "api_url": str(sec.get("api_url", "")).strip().rstrip('/'),
            "secret_key": str(sec.get("secret_key", "")).strip(),
            "bucket": str(sec.get("bucket", "")).strip(),
        }
    except Exception:
        return {"enabled":False,"api_url":"","secret_key":"","bucket":""}


def _supabase_ready():
    cfg=_supabase_cfg()
    return bool(cfg['enabled'] and cfg['api_url'] and cfg['secret_key'] and cfg['bucket'])


def _supabase_headers(extra=None):
    cfg=_supabase_cfg(); key=cfg['secret_key']
    h={"Authorization":f"Bearer {key}","apikey":key}
    if extra: h.update(extra)
    return h


def _supabase_object_url(remote_path, authenticated=False):
    cfg=_supabase_cfg()
    bucket=urllib.parse.quote(cfg['bucket'],safe='')
    path=urllib.parse.quote(str(remote_path).lstrip('/'),safe='/')
    mode='authenticated/' if authenticated else ''
    return f"{cfg['api_url']}/storage/v1/object/{mode}{bucket}/{path}"


def _is_supabase_missing_object_error(exc):
    text=str(exc or '').lower().replace(' ', '')
    markers=(
        'http404', '"statuscode":"404"', '"statuscode":404', '"code":"nosuchkey"',
        '"error":"not_found"', 'objectnotfound', 'nosuchkey', 'notfound'
    )
    return any(m in text for m in markers)


def _is_supabase_retryable_error(exc):
    text=str(exc or '').lower()
    return any(x in text for x in ('http 408','http 425','http 429','http 500','http 502','http 503','http 504',
                                           'timed out','timeout','temporarily unavailable','connection reset','urlopen error',
                                           'connection aborted','connection refused','remote end closed','unexpected eof',
                                           'temporary failure','network is unreachable','name or service not known'))


def _supabase_upload_bytes(payload,remote_path,content_type='application/octet-stream',upsert=True):
    """Upload bytes. Immutable revision objects use upsert=False; rolling convenience copies use True."""
    headers=_supabase_headers({'Content-Type':content_type,'Cache-Control':'no-store'})
    headers['x-upsert']='true' if upsert else 'false'
    last=None
    for attempt in range(SYNC_HTTP_RETRIES):
        req=urllib.request.Request(_supabase_object_url(remote_path),data=payload,method='POST',headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=25) as resp:
                return 200 <= int(getattr(resp,'status',200)) < 300
        except urllib.error.HTTPError as e:
            body=e.read().decode('utf-8','ignore')[:1200]
            last=RuntimeError(f"Supabase HTTP {e.code}: {body or e.reason}")
            if attempt+1<SYNC_HTTP_RETRIES and _is_supabase_retryable_error(last):
                time.sleep(0.6*(2**attempt)); continue
            raise last
        except (urllib.error.URLError,TimeoutError,OSError) as e:
            last=RuntimeError(f"Supabase network error: {e}")
            if attempt+1<SYNC_HTTP_RETRIES:
                time.sleep(0.6*(2**attempt)); continue
            raise last
    raise last or RuntimeError('Supabase upload failed')


def _supabase_download(remote_path,retry_missing=False):
    """Authenticated private download with bounded retry for transient/just-created objects."""
    last=None
    attempts=SYNC_HTTP_RETRIES if retry_missing else max(2,SYNC_HTTP_RETRIES-1)
    for attempt in range(attempts):
        req=urllib.request.Request(
            _supabase_object_url(remote_path,authenticated=True),method='GET',
            headers=_supabase_headers({'Cache-Control':'no-store','Pragma':'no-cache'})
        )
        try:
            with urllib.request.urlopen(req,timeout=25) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body=e.read().decode('utf-8','ignore')[:1200]
            last=RuntimeError(f"Supabase HTTP {e.code}: {body or e.reason}")
            missing=_is_supabase_missing_object_error(last)
            if attempt+1<attempts and ((retry_missing and missing) or _is_supabase_retryable_error(last)):
                time.sleep(0.5*(2**attempt)); continue
            raise last
        except (urllib.error.URLError,TimeoutError,OSError) as e:
            last=RuntimeError(f"Supabase network error: {e}")
            if attempt+1<attempts:
                time.sleep(0.5*(2**attempt)); continue
            raise last
    raise last or RuntimeError('Supabase download failed')


def _supabase_download_optional(remote_path,retry_missing=False):
    try:
        return _supabase_download(remote_path,retry_missing=retry_missing)
    except RuntimeError as e:
        if _is_supabase_missing_object_error(e): return None
        raise


def _supabase_list_files(prefix='',limit=100,offset=0,order='desc'):
    """List object metadata through Storage API (metadata plane; not CDN object cache)."""
    cfg=_supabase_cfg(); bucket=urllib.parse.quote(cfg['bucket'],safe='')
    url=f"{cfg['api_url']}/storage/v1/object/list/{bucket}"
    body=json.dumps({
        'prefix':str(prefix or '').strip('/'),'limit':int(limit),'offset':int(offset),
        'sortBy':{'column':'name','order':'desc' if str(order).lower()=='desc' else 'asc'}
    },separators=(',',':')).encode('utf-8')
    last=None
    for attempt in range(SYNC_HTTP_RETRIES):
        req=urllib.request.Request(url,data=body,method='POST',headers=_supabase_headers({'Content-Type':'application/json','Cache-Control':'no-store'}))
        try:
            with urllib.request.urlopen(req,timeout=25) as resp:
                data=json.loads(resp.read().decode('utf-8') or '[]')
                if not isinstance(data,list): raise RuntimeError('Supabase list response is not a list')
                return data
        except urllib.error.HTTPError as e:
            txt=e.read().decode('utf-8','ignore')[:1200]
            last=RuntimeError(f"Supabase HTTP {e.code}: {txt or e.reason}")
            if attempt+1<SYNC_HTTP_RETRIES and _is_supabase_retryable_error(last):
                time.sleep(0.6*(2**attempt)); continue
            raise last
        except (urllib.error.URLError,TimeoutError,OSError,json.JSONDecodeError) as e:
            last=RuntimeError(f"Supabase list error: {e}")
            if attempt+1<SYNC_HTTP_RETRIES:
                time.sleep(0.6*(2**attempt)); continue
            raise last
    raise last or RuntimeError('Supabase list failed')


def _sqlite_health(path):
    """Read-only integrity and business-row summary for recovery/sync decisions."""
    info={"valid":False,"reason":"","users":0,"active_users":0,"products":0,
          "inventory_sessions":0,"inventory_counts":0,"weekly_inventory_sessions":0,
          "weekly_inventory_captures":0,"weekly_inventory_counts":0,"movements":0,"pos_sales":0,
          "pos_batches":0,"cocktails":0,"recipes":0,"product_admin_audit":0,
          "last_session_date":None,"last_event_at":None,"size_bytes":0}
    if not path or not os.path.exists(path) or os.path.getsize(path)<=0:
        info["reason"]="missing_or_empty"; return info
    info['size_bytes']=int(os.path.getsize(path)); c=None
    try:
        c=sqlite3.connect(f"file:{os.path.abspath(path)}?mode=ro",uri=True,timeout=15)
        quick=c.execute("PRAGMA quick_check").fetchone()
        if not quick or str(quick[0]).lower()!="ok": info["reason"]="quick_check_failed"; return info
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing=RECOVERY_REQUIRED_TABLES-tables
        if missing: info["reason"]="missing_tables:"+",".join(sorted(missing)); return info
        def count_table(name): return int(c.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]) if name in tables else 0
        info['users']=count_table('users')
        info['active_users']=int(c.execute("SELECT COUNT(*) FROM users WHERE COALESCE(active,1)=1").fetchone()[0])
        for key,table in [('products','products'),('inventory_sessions','inventory_sessions'),('inventory_counts','inventory_counts'),
                          ('weekly_inventory_sessions','weekly_inventory_sessions'),('weekly_inventory_captures','weekly_inventory_captures'),
                          ('weekly_inventory_counts','weekly_inventory_counts'),('movements','movements'),('pos_sales','pos_sales'),
                          ('pos_batches','pos_batches'),('cocktails','cocktails'),('recipes','recipes'),('product_admin_audit','product_admin_audit')]:
            info[key]=count_table(table)
        r=c.execute("SELECT MAX(session_date) FROM inventory_sessions").fetchone(); info['last_session_date']=r[0] if r else None
        ev=[]
        for table in ('inventory_sessions','weekly_inventory_sessions','weekly_inventory_captures','weekly_inventory_counts','movements','pos_sales','pos_batches','product_admin_audit'):
            if table in tables:
                cols={x[1] for x in c.execute(f"PRAGMA table_info({table})").fetchall()}
                if 'created_at' in cols:
                    rr=c.execute(f"SELECT MAX(created_at) FROM {table}").fetchone()
                    if rr and rr[0]: ev.append(str(rr[0]))
        info['last_event_at']=max(ev) if ev else None
        info['valid']=True; info['reason']='ok'; return info
    except Exception as e:
        info['reason']=f"sqlite_error:{e}"; return info
    finally:
        if c is not None:
            try:c.close()
            except Exception:pass


_DIGEST_TABLES=(
    'users','categories','products','locations','inventory_sessions','inventory_counts',
    'weekly_inventory_sessions','weekly_inventory_session_products','weekly_inventory_captures','weekly_inventory_counts',
    'movements','cocktails','recipes','pos_sales','pos_batches','settings','legacy_rows','product_admin_audit'
)
_DIGEST_EXCLUDE_COLUMNS={'users':{'last_login_at'}}


def _db_data_digest(path):
    """Canonical SHA-256 of durable application data; independent from SQLite file layout/WAL."""
    if not path or not os.path.exists(path): return None
    c=None; h=hashlib.sha256()
    try:
        c=sqlite3.connect(f"file:{os.path.abspath(path)}?mode=ro",uri=True,timeout=15); c.row_factory=sqlite3.Row
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for table in _DIGEST_TABLES:
            if table not in tables: continue
            cols=[r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
            cols=[x for x in cols if x not in _DIGEST_EXCLUDE_COLUMNS.get(table,set())]
            if not cols: continue
            order_cols=['id'] if 'id' in cols else (['key'] if 'key' in cols else list(cols))
            order_sql=','.join(chr(34)+x+chr(34) for x in order_cols)
            sql=f"SELECT {','.join(chr(34)+x+chr(34) for x in cols)} FROM {chr(34)+table+chr(34)} ORDER BY {order_sql}"
            h.update((table+'\n').encode())
            for row in c.execute(sql):
                vals=[]
                for col in cols:
                    v=row[col]
                    if isinstance(v,float): v=round(v,9)
                    vals.append(v)
                h.update(json.dumps(vals,ensure_ascii=False,separators=(',',':'),default=str).encode('utf-8')); h.update(b'\n')
        return h.hexdigest()
    finally:
        if c is not None:
            try:c.close()
            except Exception:pass


def _file_sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def _read_sync_state_path(path):
    if not path or not os.path.exists(path): return None
    c=None
    try:
        c=sqlite3.connect(f"file:{os.path.abspath(path)}?mode=ro",uri=True,timeout=10)
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if 'sync_state' not in tables: return None
        c.row_factory=sqlite3.Row; r=c.execute("SELECT * FROM sync_state WHERE id=1").fetchone()
        d=dict(r) if r else None
        if d is not None: d['generation']=int(d.get('generation') or 0)
        return d
    except Exception:return None
    finally:
        if c is not None:
            try:c.close()
            except Exception:pass


def _write_sync_state_in_file(path,revision,base_digest,status='ok',message='',generation=0):
    c=sqlite3.connect(path,timeout=30)
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS sync_state(
          id INTEGER PRIMARY KEY CHECK(id=1), remote_revision TEXT, base_digest TEXT,
          last_synced_at TEXT, last_backup_status TEXT, last_backup_message TEXT, generation INTEGER DEFAULT 0)""")
        cols={r[1] for r in c.execute("PRAGMA table_info(sync_state)").fetchall()}
        if 'generation' not in cols: c.execute("ALTER TABLE sync_state ADD COLUMN generation INTEGER DEFAULT 0")
        c.execute("""INSERT INTO sync_state(id,remote_revision,base_digest,last_synced_at,last_backup_status,last_backup_message,generation)
                     VALUES(1,?,?,?,?,?,?)
                     ON CONFLICT(id) DO UPDATE SET remote_revision=excluded.remote_revision,
                       base_digest=excluded.base_digest,last_synced_at=excluded.last_synced_at,
                       last_backup_status=excluded.last_backup_status,last_backup_message=excluded.last_backup_message,
                       generation=excluded.generation""",
                  (revision,base_digest,now_iso(),status,message[:1000],int(generation or 0)))
        c.commit()
    finally:c.close()


def _health_vector(h):
    keys=('users','products','inventory_sessions','inventory_counts','weekly_inventory_sessions','weekly_inventory_captures',
          'weekly_inventory_counts','movements','pos_sales','pos_batches','cocktails','recipes','product_admin_audit')
    return tuple(int(h.get(k,0) or 0) for k in keys)


def _dominance(a,b):
    va=_health_vector(a); vb=_health_vector(b)
    if all(x>=y for x,y in zip(va,vb)) and any(x>y for x,y in zip(va,vb)): return 1
    if all(x<=y for x,y in zip(va,vb)) and any(x<y for x,y in zip(va,vb)): return -1
    return 0


def _atomic_replace_db(source_path,reason='sync'):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if os.path.exists(DB) and os.path.getsize(DB)>0:
        try:shutil.copy2(DB,f"bar_inventory_v3_before_{reason}_{stamp}.db")
        except Exception:pass
    for sidecar in (DB+'-wal',DB+'-shm'):
        try:
            if os.path.exists(sidecar):os.remove(sidecar)
        except Exception:pass
    tmp_local=DB+'.incoming'; shutil.copy2(source_path,tmp_local); os.replace(tmp_local,DB)
    for sidecar in (DB+'-wal',DB+'-shm'):
        try:
            if os.path.exists(sidecar):os.remove(sidecar)
        except Exception:pass


def _safe_sqlite_snapshot(source_path=None):
    source_path=source_path or DB
    if not os.path.exists(source_path): raise FileNotFoundError(source_path)
    fd,tmp=tempfile.mkstemp(prefix='ramona_snapshot_',suffix='.db'); os.close(fd); src=dst=None
    try:
        src=sqlite3.connect(source_path,timeout=30); src.execute('PRAGMA busy_timeout=30000')
        dst=sqlite3.connect(tmp,timeout=30); src.backup(dst); dst.commit(); dst.close(); dst=None; src.close(); src=None
        check=_sqlite_health(tmp)
        if not check['valid']: raise RuntimeError(f"Snapshot SQLite no válido: {check['reason']}")
        return tmp,check
    except Exception:
        for c in (dst,src):
            try:
                if c:c.close()
            except Exception:pass
        try:os.remove(tmp)
        except Exception:pass
        raise


def _legacy_manifest_optional():
    raw=_supabase_download_optional(SYNC_LEGACY_MANIFEST_PATH)
    if not raw:return None
    try:
        data=json.loads(raw.decode('utf-8'))
        return data if isinstance(data,dict) else None
    except Exception:return None


def _download_valid_db(remote_path,expected_digest=None,expected_sha=None,retry_missing=False):
    raw=_supabase_download_optional(remote_path,retry_missing=retry_missing)
    if raw is None:return None
    fd,tmp=tempfile.mkstemp(prefix='ramona_remote_',suffix='.db');os.close(fd)
    try:
        with open(tmp,'wb') as fh:fh.write(raw);fh.flush();os.fsync(fh.fileno())
        h=_sqlite_health(tmp)
        if not h.get('valid'):raise RuntimeError(f"Backup remoto no válido ({remote_path}): {h.get('reason')}")
        d=_db_data_digest(tmp)
        if expected_digest and d!=expected_digest:raise RuntimeError(f"Digest no coincide para {remote_path}")
        if expected_sha and _file_sha256(tmp)!=expected_sha:raise RuntimeError(f"SHA-256 no coincide para {remote_path}")
        return tmp,h,d
    except Exception:
        try:os.remove(tmp)
        except Exception:pass
        raise


def _parse_v2_meta(raw,path=''):
    try:
        m=json.loads(raw.decode('utf-8'))
        required=('revision','object_path','data_digest','generation','created_at')
        if not isinstance(m,dict) or any(m.get(k) in (None,'') for k in required):raise ValueError('metadata incompleta')
        m['generation']=int(m['generation']); m['_meta_path']=path; return m
    except Exception as e:raise RuntimeError(f"Metadata V2 inválida {path}: {e}")


def _remote_v2_head_meta():
    """Return one authoritative V2 head meta with the fewest possible Storage requests.

    Revision filenames start with a zero-padded generation. We therefore identify the highest
    generation from LIST metadata first and download only metadata files in that generation
    (normally one file). This avoids downloading 20 metadata objects on every Streamlit rerun.
    """
    items=_supabase_list_files(SYNC_V2_PREFIX,limit=100,order='desc')
    parsed=[];fallback=[]
    for item in items:
        name=str(item.get('name') or '')
        if not name.endswith('.meta.json'):continue
        m=re.match(r'^g(\d{10})_.*\.meta\.json$',name)
        if m:parsed.append((int(m.group(1)),name))
        else:fallback.append(name)
    if parsed:
        maxgen=max(g for g,_ in parsed)
        names=[name for g,name in parsed if g==maxgen]
    else:
        names=fallback[:20]
    if not names:return None
    metas=[]
    for name in names:
        path=f"{SYNC_V2_PREFIX}/{name}" if '/' not in name else name
        raw=_supabase_download_optional(path,retry_missing=True)
        if raw is None:continue
        try:metas.append(_parse_v2_meta(raw,path))
        except Exception:continue
    if not metas:return None
    maxgen=max(int(m['generation']) for m in metas)
    heads=[m for m in metas if int(m['generation'])==maxgen]
    digests={m['data_digest'] for m in heads}
    if len(digests)>1:
        raise RuntimeError(f"Conflicto remoto: existen {len(heads)} revisiones diferentes en generación {maxgen}. Ninguna será sobrescrita.")
    heads.sort(key=lambda m:(str(m.get('created_at') or ''),str(m.get('revision') or '')),reverse=True)
    return heads[0]


def _remote_legacy_best_to_temp():
    """Migration fallback: inspect manifest target + rolling latest/daily/weekly + legacy slots.
    Choose only a candidate that safely dominates the others; never guess between equal-size branches.
    """
    paths=[]; manifest=_legacy_manifest_optional()
    if manifest and manifest.get('object_path'):paths.append(str(manifest['object_path']))
    paths += [SYNC_LATEST_PATH,'revisions/slot_a.db','revisions/slot_b.db']
    for folder in ('daily','weekly'):
        try:
            for item in _supabase_list_files(folder,limit=8,order='desc')[:4]:
                name=str(item.get('name') or '')
                if name.endswith('.db'):paths.append(f"{folder}/{name}" if '/' not in name else name)
        except Exception:pass
    # de-duplicate while preserving priority
    seen=set(); paths=[p for p in paths if p and not (p in seen or seen.add(p))]
    candidates=[]
    for path in paths:
        try:
            expected_d=manifest.get('data_digest') if (manifest and path==manifest.get('object_path')) else None
            expected_s=manifest.get('file_sha256') if (manifest and path==manifest.get('object_path')) else None
            got=_download_valid_db(path,expected_d,expected_s,retry_missing=True)
            if got:
                tmp,h,d=got;candidates.append((tmp,h,d,path))
        except Exception:
            # Broken legacy objects are ignored when another valid durable candidate exists.
            continue
    if not candidates:return None,{"valid":False,"reason":"remote_missing"},None,None
    # Group equivalent copies by digest first. Several rolling files can legitimately contain
    # the exact same newest database (latest + daily + weekly + slot). They must count as one
    # logical candidate, not as several competing winners.
    groups={}
    for c in candidates:
        groups.setdefault(c[2],[]).append(c)
    if len(groups)==1:
        chosen=next(iter(groups.values()))[0]
    else:
        reps={digest:items[0] for digest,items in groups.items()}
        winning_digests=[]
        for digest,c in reps.items():
            if all(other_digest==digest or _dominance(c[1],other[1])==1
                   for other_digest,other in reps.items()):
                winning_digests.append(digest)
        if len(winning_digests)!=1:
            for c in candidates:
                try:os.remove(c[0])
                except Exception:pass
            raise RuntimeError('Conflicto entre respaldos legacy de Supabase; existen ramas distintas y ninguna domina de forma segura a las demás.')
        chosen=groups[winning_digests[0]][0]
    for c in candidates:
        if c is not chosen:
            try:os.remove(c[0])
            except Exception:pass
    tmp,h,d,path=chosen
    rev=(str(manifest.get('revision')) if manifest and path==manifest.get('object_path') and manifest.get('revision') else f"legacy-{d[:16]}")
    meta={'schema':1,'revision':rev,'generation':0,'data_digest':d,'object_path':path,
          'created_at':str((manifest or {}).get('created_at') or h.get('last_event_at') or ''),'legacy':True,'health':h}
    return tmp,h,d,meta


def _remote_revision_to_temp():
    """Return the durable remote head. V2 immutable revisions are preferred permanently."""
    if not _supabase_ready():return None,{"valid":False,"reason":"supabase_not_configured"},None,None
    meta=_remote_v2_head_meta()
    if meta:
        got=_download_valid_db(meta['object_path'],meta.get('data_digest'),meta.get('file_sha256'),retry_missing=True)
        if not got:raise RuntimeError('La revisión V2 anunciada por Storage no pudo descargarse.')
        tmp,h,d=got;return tmp,h,d,meta
    return _remote_legacy_best_to_temp()


def _preflight_supabase_sync():
    """Reconcile before SQLite opens. Genuine remote errors fail closed for WRITES, not by guessing."""
    global SYNC_PREFLIGHT_STATUS,AUTO_RECOVERY_APPLIED
    local_h=_sqlite_health(DB);SYNC_PREFLIGHT_STATUS['local_health']=local_h
    if not _supabase_ready():
        SYNC_PREFLIGHT_STATUS.update(status='offline',message='Supabase no configurado; se conserva la base local.');return False
    tmp=None
    try:
        tmp,remote_h,remote_digest,meta=_remote_revision_to_temp();SYNC_PREFLIGHT_STATUS['remote_health']=remote_h
        if not tmp or not remote_h.get('valid'):
            SYNC_PREFLIGHT_STATUS.update(status='remote_missing',message='Supabase no tiene todavía un backup válido; se permitirá inicializar desde una base local validada.');return False
        local_reset=(not local_h.get('valid') or (local_h.get('inventory_sessions',0)==0 and local_h.get('inventory_counts',0)==0 and local_h.get('users',0)<=1))
        if local_reset:
            _atomic_replace_db(tmp,'supabase_recovery');AUTO_RECOVERY_APPLIED=True
            SYNC_PREFLIGHT_STATUS.update(status='restored_remote',message='Base local ausente/reiniciada; se recuperó Supabase antes de abrir la app.',local_health=remote_h);return True
        local_digest=_db_data_digest(DB)
        if local_digest==remote_digest:
            SYNC_PREFLIGHT_STATUS.update(status='synced',message='Base local y Supabase contienen los mismos datos.');return False
        state=_read_sync_state_path(DB) or {};base_rev=str(state.get('remote_revision') or '');base_digest=str(state.get('base_digest') or '')
        remote_rev=str((meta or {}).get('revision') or '')
        # Same parent by revision OR digest means the local DB is a legitimate unsynced descendant.
        if (base_rev and base_rev==remote_rev) or (base_digest and base_digest==remote_digest):
            SYNC_PREFLIGHT_STATUS.update(status='local_ahead',message='Hay cambios locales pendientes de publicar sobre la revisión remota conocida.');return False
        if base_digest and local_digest==base_digest:
            _atomic_replace_db(tmp,'supabase_newer');AUTO_RECOVERY_APPLIED=True
            SYNC_PREFLIGHT_STATUS.update(status='restored_remote',message='Supabase era más reciente; se actualizó la base local antes de continuar.',local_health=remote_h);return True
        # Legacy DB without lineage: only strict row-count dominance is safe.
        if not base_rev and not base_digest:
            dom=_dominance(remote_h,local_h)
            if dom==1:
                _atomic_replace_db(tmp,'supabase_legacy_newer');AUTO_RECOVERY_APPLIED=True
                SYNC_PREFLIGHT_STATUS.update(status='restored_remote',message='Supabase contiene una base más completa; se recuperó automáticamente.',local_health=remote_h);return True
            if dom==-1:
                SYNC_PREFLIGHT_STATUS.update(status='local_ahead',message='La base local contiene más datos y será publicada de forma controlada.');return False
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        try:shutil.copy2(DB,f"bar_inventory_v3_sync_conflict_{stamp}.db")
        except Exception:pass
        SYNC_PREFLIGHT_STATUS.update(status='conflict',message='Local y Supabase cambiaron independientemente. Se conserva todo y se bloquean escrituras hasta revisión.');return False
    except Exception as e:
        SYNC_PREFLIGHT_STATUS.update(status='remote_error',message=f'No se pudo verificar Supabase tras varios reintentos: {e}');return False
    finally:
        if tmp:
            try:os.remove(tmp)
            except Exception:pass


def _write_sync_guard():
    """Fresh remote validation immediately before any operational write.

    Page rendering is allowed even when a transient Supabase check fails, but an inventory/POS/
    movement write is accepted only after the current local database is proven to descend from the
    current durable remote revision. If local changes are pending, they are backed up first.
    """
    if not _supabase_ready():
        return False,'Supabase no está configurado; la captura no se realizará para evitar datos sin respaldo durable.'
    remote_tmp=None
    with WRITE_SYNC_LOCK:
        try:
            local_h=_sqlite_health(DB)
            if not local_h.get('valid'):
                return False,f"La base local no superó la validación SQLite: {local_h.get('reason')}"
            remote_tmp,remote_h,remote_digest,remote_meta=_remote_revision_to_temp()
            if not remote_tmp or not remote_h.get('valid'):
                ok,msg=backup_db_to_supabase(force=True,allow_bootstrap=True)
                if not ok:return False,'No fue posible inicializar el respaldo durable antes de guardar: '+msg
                return True,'Supabase inicializado y validado.'
            local_digest=_db_data_digest(DB)
            if local_digest==remote_digest:
                return True,'Local y Supabase sincronizados.'
            state=_read_sync_state_path(DB) or {}
            base_rev=str(state.get('remote_revision') or '')
            base_digest=str(state.get('base_digest') or '')
            remote_rev=str((remote_meta or {}).get('revision') or '')
            # Local is a legitimate unsynced descendant of the current remote head. Publish it
            # before accepting another write so we never stack multiple unprotected operations.
            if (base_rev and base_rev==remote_rev) or (base_digest and base_digest==remote_digest):
                ok,msg=backup_db_to_supabase(force=True)
                if not ok:return False,'Hay cambios locales pendientes y no pudieron respaldarse antes de continuar: '+msg
                # Confirm the durable head really matches the current local data.
                try:
                    if remote_tmp:
                        os.remove(remote_tmp); remote_tmp=None
                except Exception:pass
                remote_tmp,remote_h2,remote_digest2,remote_meta2=_remote_revision_to_temp()
                if remote_tmp and remote_h2.get('valid') and remote_digest2==local_digest:
                    return True,'Cambios locales pendientes respaldados y sincronización confirmada.'
                return False,'Supabase respondió, pero no confirmó la misma versión local. Actualiza la página antes de guardar.'
            if base_digest and local_digest==base_digest:
                return False,'Supabase contiene una revisión más reciente que esta instancia. Actualiza la página para recuperar los datos antes de guardar.'
            return False,'Se detectó una posible divergencia entre esta instancia y Supabase. No se guardó nada; Developer/Owner debe revisar la sincronización.'
        except Exception as e:
            return False,f'No fue posible validar el respaldo durable en Supabase: {e}'
        finally:
            if remote_tmp:
                try:os.remove(remote_tmp)
                except Exception:pass

# ---------------------- optional Google Drive backup ----------------------
def _gdrive_cfg():
    try:
        sec=st.secrets.get("gdrive", {})
        return {"enabled": bool(sec.get("enabled", False)), "folder_id": str(sec.get("folder_id", "")).strip(), "service_account_json": str(sec.get("service_account_json", "")).strip()}
    except Exception:
        return {"enabled": False, "folder_id": "", "service_account_json": ""}

def _drive_service():
    cfg=_gdrive_cfg()
    if not (cfg["enabled"] and cfg["folder_id"] and cfg["service_account_json"]): return None
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        creds=Credentials.from_service_account_info(json.loads(cfg["service_account_json"]), scopes=["https://www.googleapis.com/auth/drive"])
        return build("drive","v3",credentials=creds,cache_discovery=False)
    except Exception:
        return None

def _find_drive_file(service,name,folder_id):
    safe=name.replace("'","\\'")
    res=service.files().list(q=f"name='{safe}' and '{folder_id}' in parents and trashed=false",spaces='drive',fields='files(id,name,modifiedTime)',pageSize=10).execute()
    files=res.get('files',[]); return files[0] if files else None

def backup_db_to_drive(force=False):
    service=_drive_service(); cfg=_gdrive_cfg()
    if not service or not os.path.exists(DB): return False,"Respaldo Drive no configurado"
    try:
        from googleapiclient.http import MediaFileUpload
        folder=cfg['folder_id']
        for name in ['bar_inventory_v3_latest.db',f"bar_inventory_v3_{local_today().isoformat()}.db"]:
            media=MediaFileUpload(DB,mimetype='application/octet-stream',resumable=False)
            found=_find_drive_file(service,name,folder)
            if found: service.files().update(fileId=found['id'],media_body=media).execute()
            else: service.files().create(body={'name':name,'parents':[folder]},media_body=media,fields='id').execute()
        st.session_state['_last_drive_backup']=local_now().isoformat(timespec='seconds')
        return True,"Respaldo actualizado en Google Drive"
    except Exception as e:
        st.session_state['_drive_backup_error']=str(e)
        return False,f"No se pudo respaldar en Drive: {e}"


def _save_conflict_snapshot(snapshot_path,local_digest,reason):
    """Best-effort durable preservation of a divergent local branch without touching authoritative revisions."""
    today=local_today().isoformat(); token=uuid.uuid4().hex[:10]
    paths=[f'conflicts/{today}_{token}_{local_digest[:12]}.db']
    try:
        with open(snapshot_path,'rb') as fh:payload=fh.read()
        for remote in paths:_supabase_upload_bytes(payload,remote,upsert=False)
        return paths[0]
    except Exception:return None


def _publish_rolling_copies_best_effort(payload):
    """Human-friendly copies only. Recovery never trusts these mutable paths in V0.5.7+."""
    warnings=[];today=local_today();iso=today.isocalendar()
    rolling=[SYNC_LATEST_PATH,f"daily/bar_inventory_{today.isoformat()}.db",f"weekly/bar_inventory_{iso.year}-W{iso.week:02d}.db"]
    for remote in rolling:
        try:_supabase_upload_bytes(payload,remote,upsert=True)
        except Exception as e:warnings.append(f"{remote}: {e}")
    return warnings


def backup_db_to_supabase(force=False,allow_bootstrap=True):
    """Publish one immutable verified V2 revision; mutable rolling files are convenience copies only."""
    if not _supabase_ready():return False,'Supabase backup no configurado'
    snap=None;remote_tmp=None
    try:
        snap,health=_safe_sqlite_snapshot();local_digest=_db_data_digest(snap);state=_read_sync_state_path(DB) or {}
        remote_tmp,remote_h,remote_digest,remote_meta=_remote_revision_to_temp()
        remote_valid=bool(remote_tmp and remote_h.get('valid'))
        legacy_equivalent=False
        if remote_valid and local_digest==remote_digest:
            if int((remote_meta or {}).get('schema') or 1)>=2:
                gen=int((remote_meta or {}).get('generation') or 0);rev=str((remote_meta or {}).get('revision') or '')
                _write_sync_state_in_file(DB,rev,local_digest,'ok','Datos ya sincronizados con Supabase',generation=gen)
                st.session_state['_last_supabase_backup']=str((remote_meta or {}).get('created_at') or local_now().isoformat(timespec='seconds'))
                st.session_state['_last_supabase_backup_health']=health;st.session_state.pop('_supabase_backup_error',None)
                SYNC_PREFLIGHT_STATUS.update(status='synced',message='Base local y Supabase contienen los mismos datos.',local_health=health,remote_health=remote_h)
                return True,f"Supabase ya sincronizado · {health['inventory_sessions']} sesiones · {health['inventory_counts']} conteos"
            # Same durable data but only legacy objects exist: publish one immutable V2 revision
            # so future recovery no longer depends on mutable latest/manifest/slot paths.
            legacy_equivalent=True
        base_rev=str(state.get('remote_revision') or '');base_digest=str(state.get('base_digest') or '')
        if remote_valid:
            remote_rev=str((remote_meta or {}).get('revision') or '')
            if base_rev or base_digest:
                if not ((base_rev and base_rev==remote_rev) or (base_digest and base_digest==remote_digest)):
                    conflict_path=_save_conflict_snapshot(snap,local_digest,'remote advanced')
                    msg='Supabase avanzó desde otra base; la copia local NO sobrescribió la revisión remota.'
                    if conflict_path:msg+=f' Copia local preservada en {conflict_path}.'
                    _write_sync_state_in_file(DB,base_rev,base_digest or local_digest,'conflict',msg,generation=int(state.get('generation') or 0))
                    st.session_state['_supabase_backup_error']=msg;return False,msg
            else:
                dom=_dominance(health,remote_h)
                if not legacy_equivalent and dom!=1:
                    conflict_path=_save_conflict_snapshot(snap,local_digest,'legacy divergence')
                    msg='Conflicto legacy detectado; no se publicó sobre Supabase.'
                    if conflict_path:msg+=f' Copia local preservada en {conflict_path}.'
                    st.session_state['_supabase_backup_error']=msg;return False,msg
        remote_gen=int((remote_meta or {}).get('generation') or 0) if remote_valid else 0
        generation=remote_gen+1;revision=uuid.uuid4().hex;created=local_now().isoformat(timespec='seconds')
        compact=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        stem=f"g{generation:010d}_{compact}_{revision}"
        revision_path=f"{SYNC_V2_PREFIX}/{stem}.db";meta_path=f"{SYNC_V2_PREFIX}/{stem}.meta.json"
        _write_sync_state_in_file(snap,revision,local_digest,'ok','Backup V2 confirmado en Supabase',generation=generation)
        file_sha=_file_sha256(snap)
        with open(snap,'rb') as fh:payload=fh.read()
        # Immutable create: no upsert, therefore no CDN overwrite window.
        _supabase_upload_bytes(payload,revision_path,upsert=False)
        verify=_supabase_download(revision_path,retry_missing=True)
        if hashlib.sha256(verify).hexdigest()!=file_sha:raise RuntimeError('La revisión V2 subida no superó verificación SHA-256')
        meta={
            'schema':2,'revision':revision,'generation':generation,
            'parent_revision':str((remote_meta or {}).get('revision') or '') if remote_valid else None,
            'created_at':created,'object_path':revision_path,'file_sha256':file_sha,
            'data_digest':local_digest,'app_version':APP_VERSION,'health':health,
        }
        _supabase_upload_bytes(json.dumps(meta,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'),meta_path,'application/json',upsert=False)
        # Verify metadata directly, then confirm Storage LIST sees an unambiguous head.
        mraw=_supabase_download(meta_path,retry_missing=True);_parse_v2_meta(mraw,meta_path)
        head=None
        for attempt in range(SYNC_HTTP_RETRIES):
            try:head=_remote_v2_head_meta()
            except RuntimeError:
                raise
            if head and int(head.get('generation') or -1)>=generation:break
            time.sleep(0.5*(2**attempt))
        if not head:raise RuntimeError('La revisión se cargó, pero Storage aún no confirmó el head V2.')
        if int(head.get('generation') or 0)>generation:
            if head.get('data_digest')!=local_digest:
                conflict_path=_save_conflict_snapshot(snap,local_digest,'concurrent newer head')
                msg='Otra escritura válida avanzó Supabase durante el respaldo; se preservó esta rama sin sobrescribirla.'
                if conflict_path:msg+=f' Copia preservada en {conflict_path}.'
                st.session_state['_supabase_backup_error']=msg;return False,msg
            revision=str(head['revision']);generation=int(head['generation'])
        elif str(head.get('revision'))!=revision:
            if head.get('data_digest')!=local_digest:
                raise RuntimeError(f"Conflicto remoto detectado en generación {generation}; ambas revisiones quedan preservadas.")
            revision=str(head['revision'])
        _write_sync_state_in_file(DB,revision,local_digest,'ok','Backup V2 confirmado en Supabase',generation=generation)
        rolling_warnings=_publish_rolling_copies_best_effort(payload)
        st.session_state['_last_supabase_backup']=created;st.session_state['_last_supabase_backup_health']=health;st.session_state.pop('_supabase_backup_error',None)
        SYNC_PREFLIGHT_STATUS.update(status='synced',message='Escritura respaldada y sincronizada con Supabase.',local_health=health,remote_health=health)
        suffix=(' · copias rolling pendientes' if rolling_warnings else '')
        return True,f"Backup Supabase V2 OK · {health['inventory_sessions']} sesiones · {health['inventory_counts']} conteos · gen {generation}{suffix}"
    except Exception as e:
        st.session_state['_supabase_backup_error']=str(e)
        if SYNC_PREFLIGHT_STATUS.get('status')!='conflict':
            SYNC_PREFLIGHT_STATUS.update(status='remote_error',message=f'Backup durable pendiente: {e}')
        return False,f"No se pudo confirmar el respaldo durable en Supabase: {e}"
    finally:
        for p in (snap,remote_tmp):
            if p:
                try:os.remove(p)
                except Exception:pass


def restore_latest_from_supabase_to_temp():
    tmp,h,d,m=_remote_revision_to_temp()
    if h.get('valid'):
        h=dict(h);h['data_digest']=d;h['revision']=(m.get('revision') if m else None);h['generation']=int((m or {}).get('generation') or 0);h['v2']=bool((m or {}).get('schema')==2)
    return tmp,h


def backup_db(force=False):
    """Primary backup dispatcher. Supabase is authoritative when configured."""
    if _supabase_ready():return backup_db_to_supabase(force=force)
    return backup_db_to_drive(force=force)


# ---------------------- embedded/legacy recovery fallbacks ----------------------
def _write_embedded_recovery_snapshot(dest):
    payload=gzip.decompress(base64.b64decode("".join(RECOVERY_SNAPSHOT_GZIP_B64.split())))
    if hashlib.sha256(payload).hexdigest()!=RECOVERY_SNAPSHOT_SHA256:
        raise RuntimeError("La huella del respaldo de recuperación no coincide.")
    tmp=dest+".recovery_tmp"
    with open(tmp,"wb") as fh:
        fh.write(payload); fh.flush(); os.fsync(fh.fileno())
    check=_sqlite_health(tmp)
    if not check["valid"]:
        try: os.remove(tmp)
        except Exception: pass
        raise RuntimeError("El respaldo integrado no superó la validación SQLite.")
    os.replace(tmp,dest)
    return check


def restore_db_from_embedded_snapshot_if_reset():
    """LAST RESORT only when Supabase could not provide a valid recovery DB."""
    global AUTO_RECOVERY_APPLIED
    health=_sqlite_health(DB)
    should_restore=(not health["valid"] or (health["inventory_sessions"]==0 and health["inventory_counts"]==0 and health["users"]<=1))
    if not should_restore: return False
    if _supabase_ready() and SYNC_PREFLIGHT_STATUS.get('remote_health',{}).get('valid'):
        # Never downgrade from an embedded historical snapshot when durable Supabase exists.
        return False
    if os.path.exists(DB) and os.path.getsize(DB)>0:
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        try: shutil.copy2(DB,f"bar_inventory_v3_before_auto_recovery_{stamp}.db")
        except Exception: pass
    _write_embedded_recovery_snapshot(DB); AUTO_RECOVERY_APPLIED=True
    return True


def restore_db_from_drive_if_missing():
    # Drive is contingency only and must never override a valid Supabase recovery source.
    if os.path.exists(DB) and os.path.getsize(DB)>0: return False
    if _supabase_ready() and SYNC_PREFLIGHT_STATUS.get('remote_health',{}).get('valid'): return False
    service=_drive_service(); cfg=_gdrive_cfg()
    if not service: return False
    try:
        from googleapiclient.http import MediaIoBaseDownload
        found=_find_drive_file(service,'bar_inventory_v3_latest.db',cfg['folder_id'])
        if not found: return False
        fd,tmp=tempfile.mkstemp(prefix='ramona_drive_restore_',suffix='.db'); os.close(fd)
        request=service.files().get_media(fileId=found['id'])
        fh=io.FileIO(tmp,'wb'); dl=MediaIoBaseDownload(fh,request); done=False
        while not done: _,done=dl.next_chunk()
        fh.close()
        if not _sqlite_health(tmp).get('valid'):
            os.remove(tmp); return False
        _atomic_replace_db(tmp,'drive_recovery'); os.remove(tmp)
        return True
    except Exception:
        return False


# Every Streamlit script run reaches this point before opening SQLite. Therefore a newly
# started/stale runtime is reconciled with durable storage before any page reads or writes.
_preflight_supabase_sync()
if not os.path.exists(DB) or not _sqlite_health(DB).get('valid'):
    restore_db_from_drive_if_missing()
if not os.path.exists(DB) or not _sqlite_health(DB).get('valid'):
    restore_db_from_embedded_snapshot_if_reset()

# --------------------------- DB ---------------------------
def db():
    # One connection per Streamlit script run avoids keeping a handle to an obsolete SQLite
    # inode after an automatic/manual recovery. WAL + busy_timeout improve safe concurrent use.
    c = sqlite3.connect(DB, check_same_thread=False, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA busy_timeout=30000")
    try: c.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError: pass
    c.execute("PRAGMA synchronous=FULL")
    return c
con = db()

def q(sql, p=()): return con.execute(sql, p).fetchall()
def one(sql, p=()): return con.execute(sql, p).fetchone()
def ex(sql, p=(), do_backup=True):
    con.execute(sql, p); con.commit()
    if do_backup: backup_db()

def hash_pin(pin): return hashlib.sha256(pin.encode()).hexdigest()

def init_db():
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, pin_hash TEXT NOT NULL DEFAULT '', email TEXT UNIQUE,
      role TEXT NOT NULL CHECK(role IN ('STAFF','MANAGER','GENERAL_MANAGER','ADMIN')), active INTEGER DEFAULT 1,
      report_access INTEGER DEFAULT 0, last_login_at TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS categories(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, count_unit TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS products(
      id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL, name TEXT NOT NULL,
      bottle_ml REAL, package_type TEXT DEFAULT 'Botella', active INTEGER DEFAULT 1, daily_inventory INTEGER DEFAULT 0,
      UNIQUE(name,bottle_ml,package_type), FOREIGN KEY(category_id) REFERENCES categories(id));
    CREATE TABLE IF NOT EXISTS locations(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
    CREATE TABLE IF NOT EXISTS inventory_sessions(
      id INTEGER PRIMARY KEY, session_date TEXT NOT NULL, session_type TEXT NOT NULL,
      user_id INTEGER, created_at TEXT NOT NULL, submitted INTEGER DEFAULT 1, notes TEXT, inventory_cycle TEXT DEFAULT 'DAILY',
      paired_opening_session_id INTEGER,
      FOREIGN KEY(user_id) REFERENCES users(id),
      FOREIGN KEY(paired_opening_session_id) REFERENCES inventory_sessions(id));
    CREATE TABLE IF NOT EXISTS inventory_counts(
      id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
      location_id INTEGER NOT NULL, qty_base REAL NOT NULL, previous_qty REAL,
      variance REAL, observation TEXT,
      FOREIGN KEY(session_id) REFERENCES inventory_sessions(id),
      FOREIGN KEY(product_id) REFERENCES products(id), FOREIGN KEY(location_id) REFERENCES locations(id));
    CREATE TABLE IF NOT EXISTS movements(
      id INTEGER PRIMARY KEY, movement_date TEXT NOT NULL, movement_type TEXT NOT NULL,
      product_id INTEGER NOT NULL, qty_base REAL NOT NULL, from_location_id INTEGER,
      to_location_id INTEGER, user_id INTEGER, supplier TEXT, reference TEXT,
      observation TEXT, created_at TEXT NOT NULL,
      FOREIGN KEY(product_id) REFERENCES products(id));
    CREATE TABLE IF NOT EXISTS cocktails(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS recipes(
      id INTEGER PRIMARY KEY, cocktail_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
      oz_qty REAL NOT NULL, UNIQUE(cocktail_id,product_id));
    CREATE TABLE IF NOT EXISTS pos_sales(
      id INTEGER PRIMARY KEY, sale_date TEXT NOT NULL, cocktail_id INTEGER, product_id INTEGER,
      sale_type TEXT NOT NULL, quantity REAL NOT NULL, oz_per_unit REAL,
      user_id INTEGER, observation TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS pos_batches(
      id INTEGER PRIMARY KEY, sale_date TEXT NOT NULL, sale_group TEXT NOT NULL,
      user_id INTEGER, note TEXT, created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS legacy_rows(
      id INTEGER PRIMARY KEY, source_sheet TEXT, source_row INTEGER, raw_text TEXT,
      imported_at TEXT NOT NULL);
    """)
    # Migración compatible desde bases anteriores: añade campos de autenticación Google si faltan.
    cols={r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()}
    if "email" not in cols: con.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "last_login_at" not in cols: con.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")
    if "created_at" not in cols: con.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
    if "report_access" not in cols: con.execute("ALTER TABLE users ADD COLUMN report_access INTEGER DEFAULT 0")
    pcols={r[1] for r in con.execute("PRAGMA table_info(products)").fetchall()}
    if "unit_cost" not in pcols: con.execute("ALTER TABLE products ADD COLUMN unit_cost REAL")
    try: con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL")
    except sqlite3.OperationalError: pass
    for n,u in [("Cerveza","bottle"),("Licor","oz"),("Cócteles","sale")]:
        con.execute("INSERT OR IGNORE INTO categories(name,count_unit) VALUES(?,?)", (n,u))
    for n in ["Bar","Bodega"]:
        con.execute("INSERT OR IGNORE INTO locations(name) VALUES(?)", (n,))
    if not one("SELECT 1 FROM users"):
        con.execute("INSERT INTO users(name,pin_hash,role,created_at) VALUES(?,?,?,?)", ("Admin","","ADMIN",now_iso()))
    defaults = {"safety_stock_pct":"15","tolerance_beer":"1","tolerance_liquor":"1"}
    for k,v in defaults.items(): con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    con.commit()

init_db()

# V0.3.7 migration: new GENERAL_MANAGER role, inventory frequency and daily-liquor flags.
def ensure_v037_schema():
    # Existing V0.3.x databases have a CHECK constraint that does not include GENERAL_MANAGER.
    # Rebuild only the users table while preserving IDs so all historical references remain valid.
    row=one("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    users_sql=(row['sql'] if row and row['sql'] else '')
    if 'GENERAL_MANAGER' not in users_sql:
        con.commit()
        con.execute("PRAGMA foreign_keys=OFF")
        try:
            con.execute("BEGIN")
            con.execute("""CREATE TABLE users_new(
              id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, pin_hash TEXT NOT NULL DEFAULT '', email TEXT UNIQUE,
              role TEXT NOT NULL CHECK(role IN ('STAFF','MANAGER','GENERAL_MANAGER','ADMIN')), active INTEGER DEFAULT 1,
              report_access INTEGER DEFAULT 0, last_login_at TEXT, created_at TEXT)""")
            con.execute("""INSERT INTO users_new(id,name,pin_hash,email,role,active,report_access,last_login_at,created_at)
                           SELECT id,name,COALESCE(pin_hash,''),email,role,active,COALESCE(report_access,0),last_login_at,created_at FROM users""")
            con.execute("DROP TABLE users")
            con.execute("ALTER TABLE users_new RENAME TO users")
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL")
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.execute("PRAGMA foreign_keys=ON")

    pcols={r[1] for r in con.execute("PRAGMA table_info(products)").fetchall()}
    if 'daily_inventory' not in pcols:
        con.execute("ALTER TABLE products ADD COLUMN daily_inventory INTEGER DEFAULT 0")

    scols={r[1] for r in con.execute("PRAGMA table_info(inventory_sessions)").fetchall()}
    if 'inventory_cycle' not in scols:
        con.execute("ALTER TABLE inventory_sessions ADD COLUMN inventory_cycle TEXT DEFAULT 'DAILY'")

    con.commit()

ensure_v037_schema()

# V0.3.4 migration: preserve bottle-equivalent counts when ml is still pending.
def ensure_v033_schema():
    cols={r[1] for r in con.execute("PRAGMA table_info(inventory_counts)").fetchall()}
    if 'qty_bottle_equiv' not in cols: con.execute("ALTER TABLE inventory_counts ADD COLUMN qty_bottle_equiv REAL")
    mcols={r[1] for r in con.execute("PRAGMA table_info(movements)").fetchall()}
    if 'qty_bottle_equiv' not in mcols: con.execute("ALTER TABLE movements ADD COLUMN qty_bottle_equiv REAL")
    con.commit()
ensure_v033_schema()

# V0.4.8 migration: preserve the exact opening session used by a closing.
def ensure_v048_schema():
    scols={r[1] for r in con.execute("PRAGMA table_info(inventory_sessions)").fetchall()}
    if 'paired_opening_session_id' not in scols:
        con.execute("ALTER TABLE inventory_sessions ADD COLUMN paired_opening_session_id INTEGER")
    # Read-path indexes only; no historical rows are modified or deleted.
    con.execute("CREATE INDEX IF NOT EXISTS idx_inv_sessions_date_type_cycle_created ON inventory_sessions(session_date,session_type,inventory_cycle,created_at)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_inv_counts_session_product_location ON inventory_counts(session_id,product_id,location_id)")
    # Safe metadata backfill for existing closings: link each one to the latest opening
    # of the same date/cycle that existed when the closing was saved. Counts remain untouched.
    con.execute("""UPDATE inventory_sessions AS c
                 SET paired_opening_session_id=(
                    SELECT o.id FROM inventory_sessions o
                    WHERE o.session_date=c.session_date AND o.session_type='OPENING'
                      AND COALESCE(o.inventory_cycle,'DAILY')=COALESCE(c.inventory_cycle,'DAILY')
                      AND o.created_at<=c.created_at
                    ORDER BY o.created_at DESC,o.id DESC LIMIT 1)
                 WHERE c.session_type='CLOSING' AND c.paired_opening_session_id IS NULL""")
    con.commit()
ensure_v048_schema()

# V0.5.3 migration: audit trail for product deletion / merge / deactivation.
def ensure_v053_schema():
    con.execute("""CREATE TABLE IF NOT EXISTS product_admin_audit(
      id INTEGER PRIMARY KEY, action TEXT NOT NULL, source_product_id INTEGER, source_name TEXT,
      target_product_id INTEGER, target_name TEXT, user_id INTEGER, created_at TEXT NOT NULL, details TEXT
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_product_admin_audit_created ON product_admin_audit(created_at)")
    con.commit()
ensure_v053_schema()

# V0.5.7 migration: durable synchronization lineage with immutable Supabase revisions.
def ensure_v057_schema():
    con.execute("""CREATE TABLE IF NOT EXISTS sync_state(
      id INTEGER PRIMARY KEY CHECK(id=1), remote_revision TEXT, base_digest TEXT,
      last_synced_at TEXT, last_backup_status TEXT, last_backup_message TEXT, generation INTEGER DEFAULT 0)""")
    cols={r[1] for r in con.execute("PRAGMA table_info(sync_state)").fetchall()}
    if 'generation' not in cols:con.execute("ALTER TABLE sync_state ADD COLUMN generation INTEGER DEFAULT 0")
    con.commit()
ensure_v057_schema()

# V0.5.9 migration: independent weekly physical inventory, separated from daily Opening/Closing.
def ensure_v059_schema():
    con.executescript("""
    CREATE TABLE IF NOT EXISTS weekly_inventory_sessions(
      id INTEGER PRIMARY KEY, inventory_date TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'IN_PROGRESS'
        CHECK(status IN ('IN_PROGRESS','COMPLETED')),
      started_by_user_id INTEGER, started_at TEXT NOT NULL, completed_by_user_id INTEGER, completed_at TEXT, notes TEXT,
      FOREIGN KEY(started_by_user_id) REFERENCES users(id),
      FOREIGN KEY(completed_by_user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS weekly_inventory_session_products(
      weekly_session_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
      PRIMARY KEY(weekly_session_id,product_id),
      FOREIGN KEY(weekly_session_id) REFERENCES weekly_inventory_sessions(id) ON DELETE CASCADE,
      FOREIGN KEY(product_id) REFERENCES products(id));
    CREATE TABLE IF NOT EXISTS weekly_inventory_captures(
      id INTEGER PRIMARY KEY, weekly_session_id INTEGER NOT NULL, user_id INTEGER, created_at TEXT NOT NULL,
      scope TEXT, observation TEXT,
      FOREIGN KEY(weekly_session_id) REFERENCES weekly_inventory_sessions(id) ON DELETE CASCADE,
      FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS weekly_inventory_counts(
      id INTEGER PRIMARY KEY, capture_id INTEGER NOT NULL, weekly_session_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
      location_id INTEGER NOT NULL, qty_base REAL NOT NULL, qty_bottle_equiv REAL, observation TEXT,
      user_id INTEGER, created_at TEXT NOT NULL,
      FOREIGN KEY(capture_id) REFERENCES weekly_inventory_captures(id) ON DELETE CASCADE,
      FOREIGN KEY(weekly_session_id) REFERENCES weekly_inventory_sessions(id) ON DELETE CASCADE,
      FOREIGN KEY(product_id) REFERENCES products(id), FOREIGN KEY(location_id) REFERENCES locations(id),
      FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE UNIQUE INDEX IF NOT EXISTS idx_weekly_one_active ON weekly_inventory_sessions(status) WHERE status='IN_PROGRESS';
    CREATE INDEX IF NOT EXISTS idx_weekly_sessions_date_status ON weekly_inventory_sessions(inventory_date,status,started_at);
    CREATE INDEX IF NOT EXISTS idx_weekly_counts_session_product ON weekly_inventory_counts(weekly_session_id,product_id,created_at,id);
    CREATE INDEX IF NOT EXISTS idx_weekly_captures_session_created ON weekly_inventory_captures(weekly_session_id,created_at,id);
    """)
    con.commit()
ensure_v059_schema()


def _align_or_bootstrap_sync_state():
    """After migrations, align lineage or publish a pending legitimate local descendant."""
    if not _supabase_ready():return
    # Do not immediately repeat a failed read-time network check on the same Streamlit rerun.
    # A real write will use _write_sync_guard(), which performs its own fresh retry sequence.
    if SYNC_PREFLIGHT_STATUS.get('status')=='remote_error':return
    tmp=None
    try:
        digest=_db_data_digest(DB);tmp,rh,rd,meta=_remote_revision_to_temp()
        if tmp and rh.get('valid') and digest==rd:
            if int((meta or {}).get('schema') or 1)>=2:
                _write_sync_state_in_file(DB,str((meta or {}).get('revision') or ''),digest,'ok','Sincronización verificada al iniciar',generation=int((meta or {}).get('generation') or 0));return
            # Migrate an equivalent legacy backup to one immutable V2 revision.
            backup_db_to_supabase(force=True,allow_bootstrap=True);return
        status=SYNC_PREFLIGHT_STATUS.get('status')
        if status in ('remote_missing','local_ahead'):
            backup_db_to_supabase(force=True,allow_bootstrap=True)
        elif status=='synced' and tmp and rh.get('valid') and digest!=rd:
            # A code/schema migration may legitimately change the canonical digest after the
            # preflight ran (V0.5.9 adds empty weekly tables). Publish only when the local DB
            # still declares the current remote head as its parent; this is a safe descendant,
            # not a competing business-data branch.
            state=_read_sync_state_path(DB) or {}
            remote_rev=str((meta or {}).get('revision') or '')
            if (state.get('remote_revision') and str(state.get('remote_revision'))==remote_rev) or (state.get('base_digest') and str(state.get('base_digest'))==rd):
                backup_db_to_supabase(force=True)
    except Exception as e:
        try:st.session_state['_supabase_backup_error']=str(e)
        except Exception:pass
    finally:
        if tmp:
            try:os.remove(tmp)
            except Exception:pass

# ---------------------- catalog seed from current sheet ----------------------
BEERS = ["Corona","Corona Sunbrew","XX","Negra","Especial","Sol","Coors","Molson"]
LIQUORS = [
"Jose Cuervo Silver","Jose Cuervo Gold","1800 Cristalino","Jose Cuervo Tradicional Plata","Patron Silver",
"Patron Reposado","Patron Añejo","Casamigos Añejo","Casamigos Blanco","Casamigos Reposado","Don Julio Añejo",
"Don Julio Reposado","Don Julio Blanco","Patron Cristalino","Don Julio 70","Don Julio 1942","Reserva Extra Añejo",
"1800 Blanco","1800 Reposado","1800 Coco","Herradura","Los Arango","Casa Azul","Mezcal Ilegal","Mezcal Vida",
"Mezcal Don Ramon","Mezcal Zapata","Captain Morgan White","Captain Morgan Dark","Havana Club","Triple Sec McGuinness",
"Grand Marnier","Baileys","Blue Curacao","Aperol","Crema de Cacao","Canton Ginger Liqueur","Bombay Gin","Gin True",
"Vodka True","Absolut Vodka","Grey Goose Vodka","Hendrick's Gin","Johnnie Walker Black Label","Crown Royal","Cachaça",
"Disaronno","Piña Jalapeño Tequila","Cabernet Sauvignon","Pinot Noir","Merlot","Sauvignon Blanc","Chardonnay","Pinot Grigio"
]

def seed_catalog():
    if one("SELECT COUNT(*) n FROM products")["n"] > 0: return
    cid_beer = one("SELECT id FROM categories WHERE name='Cerveza'")["id"]
    cid_liq = one("SELECT id FROM categories WHERE name='Licor'")["id"]
    for n in BEERS: con.execute("INSERT OR IGNORE INTO products(category_id,name,bottle_ml,package_type) VALUES(?,?,NULL,'Botella')",(cid_beer,n))
    for n in LIQUORS: con.execute("INSERT OR IGNORE INTO products(category_id,name,bottle_ml,package_type) VALUES(?,?,NULL,'Botella')",(cid_liq,n))
    con.commit()
seed_catalog()

def seed_daily_inventory_defaults():
    """Mark the current seven main liquors once; admins can change this list later."""
    if one("SELECT value FROM settings WHERE key='daily_inventory_defaults_seeded'"):
        return
    principal=[
        'Jose Cuervo Silver','Jose Cuervo Gold','Triple Sec McGuinness','Mezcal Ilegal',
        'Captain Morgan Dark','Captain Morgan White','Vodka True'
    ]
    for name in principal:
        con.execute("UPDATE products SET daily_inventory=1 WHERE lower(name)=lower(?)",(name,))
    con.execute("INSERT INTO settings(key,value) VALUES('daily_inventory_defaults_seeded','1')")
    con.commit()
seed_daily_inventory_defaults()

def seed_sheet_history():
    """Carga una sola vez los registros históricos que pueden interpretarse con suficiente certeza
    del Google Sheet recibido (agosto 2026). No fuerza interpretaciones sobre filas ambiguas."""
    if one("SELECT value FROM settings WHERE key='sheet_history_seeded'"):
        return
    admin=one("SELECT id FROM users WHERE name='Admin'")['id']
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    def pid(name):
        r=one("SELECT id FROM products WHERE lower(name)=lower(?) ORDER BY id LIMIT 1",(name,))
        return r['id'] if r else None
    def session(ds,kind,items):
        cur=con.execute("INSERT INTO inventory_sessions(session_date,session_type,user_id,created_at,notes) VALUES(?,?,?,?,?)",
                        (ds,kind,admin,f"{ds}T23:00:00","Importado del Google Sheet recibido"))
        sid=cur.lastrowid
        for name,qty in items.items():
            x=pid(name)
            if x is not None:
                con.execute("INSERT INTO inventory_counts(session_id,product_id,location_id,qty_base) VALUES(?,?,?,?)",(sid,x,bar,float(qty)))
    # Cervezas: el archivo contiene conteo inicial/final explícito. Se conserva el físico,
    # aunque alguna fórmula manual del Sheet sea inconsistente; la V0.2 recalcula desde los conteos.
    beer_days={
      '2026-08-21':({'Corona':132,'Corona Sunbrew':34,'XX':45,'Negra':27,'Especial':26,'Sol':57,'Coors':32,'Molson':15},{'Corona':112,'Corona Sunbrew':33,'XX':45,'Negra':25,'Especial':17,'Sol':55,'Coors':28,'Molson':15}),
      '2026-08-22':({'Corona':112,'Corona Sunbrew':33,'XX':45,'Negra':27,'Especial':20,'Sol':55,'Coors':28,'Molson':15},{'Corona':103,'Corona Sunbrew':30,'XX':40,'Negra':17,'Especial':2,'Sol':53,'Coors':27,'Molson':15}),
      '2026-08-23':({'Corona':103,'Corona Sunbrew':30,'XX':40,'Negra':17,'Especial':2,'Sol':53,'Coors':27,'Molson':15},{'Corona':96,'Corona Sunbrew':28,'XX':39,'Negra':15,'Especial':1,'Sol':51,'Coors':27,'Molson':15}),
      '2026-08-24':({'Corona':96,'Corona Sunbrew':28,'XX':39,'Negra':15,'Especial':1,'Sol':51,'Coors':26,'Molson':15},{'Corona':89,'Corona Sunbrew':27,'XX':28,'Negra':12,'Especial':0,'Sol':48,'Coors':26,'Molson':9}),
      '2026-08-25':({'Corona':89,'Corona Sunbrew':27,'XX':32,'Negra':12,'Especial':0,'Sol':48,'Coors':26,'Molson':9},{'Corona':83,'Corona Sunbrew':25,'XX':28,'Negra':8,'Especial':0,'Sol':41,'Coors':26,'Molson':7}),
      '2026-08-26':({'Corona':83,'Corona Sunbrew':26,'XX':30,'Negra':8,'Especial':0,'Sol':50,'Coors':26,'Molson':7},{'Corona':83,'Corona Sunbrew':23,'XX':30,'Negra':6,'Especial':0,'Sol':48,'Coors':25,'Molson':7}),
      '2026-08-27':({'Corona':83,'Corona Sunbrew':23,'XX':29,'Negra':6,'Especial':0,'Sol':48,'Coors':25,'Molson':7},{'Corona':78,'Corona Sunbrew':23,'XX':21,'Negra':4,'Especial':0,'Sol':47,'Coors':23,'Molson':6}),
      '2026-08-28':({'Corona':78,'Corona Sunbrew':23,'XX':21,'Negra':4,'Especial':0,'Sol':47,'Coors':23,'Molson':6},{'Corona':120,'Corona Sunbrew':23,'XX':8,'Negra':0,'Especial':0,'Sol':46,'Coors':23,'Molson':5}),
    }
    for ds,(op,cl) in beer_days.items(): session(ds,'OPENING',op); session(ds,'CLOSING',cl)
    # 29 de agosto solo tiene conteo inicial en el archivo.
    session('2026-08-29','OPENING',{'Corona':114,'Corona Sunbrew':23,'XX':28,'Negra':24,'Especial':0,'Sol':45,'Coors':45,'Molson':5})
    # POS de cervezas disponible explícitamente en el Sheet.
    beer_pos={
      '2026-08-22':{'Corona':6,'Corona Sunbrew':3,'XX':0,'Negra':7,'Especial':8,'Sol':2,'Coors':1,'Molson':0},
      '2026-08-23':{'Corona':7,'Corona Sunbrew':2,'XX':2,'Negra':1,'Especial':1,'Sol':2,'Coors':0,'Molson':0},
      '2026-08-24':{'Corona':7,'Corona Sunbrew':1,'XX':6,'Negra':3,'Especial':1,'Sol':3,'Coors':0,'Molson':6},
      '2026-08-25':{'Corona':6,'Corona Sunbrew':2,'XX':0,'Negra':4,'Especial':0,'Sol':0,'Coors':0,'Molson':2},
      '2026-08-26':{'Corona':0,'Corona Sunbrew':2,'XX':0,'Negra':2,'Especial':0,'Sol':2,'Coors':1,'Molson':0},
    }
    for ds,items in beer_pos.items():
        for name,qty in items.items():
            x=pid(name)
            if x is not None:
                con.execute("INSERT INTO pos_sales(sale_date,product_id,sale_type,quantity,user_id,created_at,observation) VALUES(?,?,?,?,?,?,?)",
                            (ds,x,'Cerveza',float(qty),admin,f"{ds}T23:30:00",'Importado del Google Sheet'))
    # Licores: se importan únicamente filas donde la interpretación apertura/cierre es razonablemente clara.
    liq22_open={'Jose Cuervo Silver':220.5,'Jose Cuervo Gold':204,'Triple Sec McGuinness':181.5,'Captain Morgan Dark':86.5,'Captain Morgan White':67.8,'Mezcal Ilegal':39.1}
    liq22_close={'Jose Cuervo Silver':136,'Jose Cuervo Gold':204,'Triple Sec McGuinness':157.3,'Captain Morgan Dark':84,'Captain Morgan White':51,'Mezcal Ilegal':39.1}
    session('2026-08-22','OPENING',liq22_open); session('2026-08-22','CLOSING',liq22_close)
    liq23_open={'Jose Cuervo Silver':136,'Jose Cuervo Gold':204,'Triple Sec McGuinness':157.3,'Captain Morgan Dark':84,'Captain Morgan White':51,'Mezcal Ilegal':39.1}
    liq23_close={'Jose Cuervo Silver':85,'Jose Cuervo Gold':204,'Triple Sec McGuinness':141.5,'Captain Morgan Dark':88.5,'Captain Morgan White':40.8,'Mezcal Ilegal':38.4}
    session('2026-08-23','OPENING',liq23_open); session('2026-08-23','CLOSING',liq23_close)
    session('2026-08-24','OPENING',{'Jose Cuervo Silver':51,'Jose Cuervo Gold':204,'Triple Sec McGuinness':124.2,'Captain Morgan Dark':60,'Captain Morgan White':37.4,'Mezcal Ilegal':32.2})
    # Las demás filas se conservan como nota de procedencia, sin convertirlas en movimientos inventados.
    con.execute("INSERT INTO legacy_rows(source_sheet,source_row,raw_text,imported_at) VALUES(?,?,?,?)",
                ('INVENTARIO DIARIO',2,'Filas iniciales del día 21 contienen inventario/entradas pero no cierre completo; conservadas para revisión manual.',now_iso()))
    con.execute("INSERT INTO settings(key,value) VALUES('sheet_history_seeded','1')")
    con.commit()
seed_sheet_history()
# Backfill pairing metadata for any rows seeded on a brand-new database.
ensure_v048_schema()
# Only after all one-time seeds/migrations have completed do we establish or advance the
# Supabase synchronization baseline. This prevents publishing a half-initialized database.
_align_or_bootstrap_sync_state()

# --------------------------- helpers ---------------------------
def setting(k, default):
    r=one("SELECT value FROM settings WHERE key=?",(k,)); return r["value"] if r else default

def products(cat=None, active=True):
    sql="SELECT p.*,c.name category,c.count_unit FROM products p JOIN categories c ON c.id=p.category_id WHERE 1=1"; ps=[]
    if active: sql += " AND p.active=1"
    if cat: sql += " AND c.name=?"; ps.append(cat)
    return q(sql+" ORDER BY c.name,p.name,COALESCE(p.bottle_ml,0)",ps)

def inventory_products(cycle='DAILY'):
    """Products required for the selected physical inventory cycle.
    DAILY = all beers + main liquors. WEEKLY = all beers + all liquors.
    """
    all_items=[p for p in products() if p['category'] in ('Cerveza','Licor')]
    if cycle=='WEEKLY':
        return all_items
    return [p for p in all_items if p['category']=='Cerveza' or int(p['daily_inventory'] or 0)==1]

def latest_opening_cycle(ds):
    r=one("""SELECT COALESCE(inventory_cycle,'DAILY') cycle FROM inventory_sessions
             WHERE session_date=? AND session_type='OPENING' ORDER BY created_at DESC LIMIT 1""",(ds,))
    return str(r['cycle']) if r else None

def normalized_text(v):
    """Normalize names for safe catalog matching without changing stored display names."""
    txt=str(v or '').strip().lower()
    txt=''.join(ch for ch in unicodedata.normalize('NFKD',txt) if not unicodedata.combining(ch))
    txt=re.sub(r'[^a-z0-9]+',' ',txt)
    return re.sub(r'\s+',' ',txt).strip()

RECIPE_LIQUOR_ALIASES={
    'triple sec':'Triple Sec McGuinness',
    'mezcal':'Mezcal Ilegal',
    'ron negro':'Captain Morgan Dark',
    'ron oscuro':'Captain Morgan Dark',
    'ron blanco':'Captain Morgan White',
    'vodake true':'Vodka True',
    'vodka true':'Vodka True',
    'jose cuervo silver':'Jose Cuervo Silver',
    'jose cuervo gold':'Jose Cuervo Gold',
}

def recipe_product_match(raw_name):
    """Match a recipe liquor name to an active liquor product; ambiguous names are not guessed."""
    key=normalized_text(raw_name)
    if not key: return None
    liquor_rows=products('Licor')
    exact={normalized_text(r['name']):r for r in liquor_rows}
    if key in exact: return exact[key]
    alias=RECIPE_LIQUOR_ALIASES.get(key)
    if alias:
        return next((r for r in liquor_rows if normalized_text(r['name'])==normalized_text(alias)),None)
    return None

ROLE_LABELS={'STAFF':'STAFF','MANAGER':'MANAGER','GENERAL_MANAGER':'MANAGER GENERAL','ADMIN':'ADMIN'}

def product_label(p):
    ml = f" · {int(p['bottle_ml'])} ml" if p['bottle_ml'] else ""
    pkg = f" · {p['package_type']}" if p['package_type'] and p['package_type'] != 'Botella' else ""
    return f"{p['name']}{ml}{pkg}"

def product_usage_summary(pid):
    """Return all references to a product before any destructive catalog action.

    A row whose quantity is 0 is still a historical reference.  V0.5.3 therefore
    distinguishes total references from references with a non-zero business value.
    """
    pid=int(pid)
    inv=one("""SELECT COUNT(*) rows,
                      SUM(CASE WHEN ABS(COALESCE(qty_base,0))>1e-9 OR ABS(COALESCE(qty_bottle_equiv,0))>1e-9 THEN 1 ELSE 0 END) nonzero
               FROM inventory_counts WHERE product_id=?""",(pid,))
    mov=one("""SELECT COUNT(*) rows,
                      SUM(CASE WHEN ABS(COALESCE(qty_base,0))>1e-9 OR ABS(COALESCE(qty_bottle_equiv,0))>1e-9 THEN 1 ELSE 0 END) nonzero
               FROM movements WHERE product_id=?""",(pid,))
    pos=one("""SELECT COUNT(*) rows,
                      SUM(CASE WHEN ABS(COALESCE(quantity,0))>1e-9 THEN 1 ELSE 0 END) nonzero
               FROM pos_sales WHERE product_id=?""",(pid,))
    rec=one("""SELECT COUNT(*) rows,
                      SUM(CASE WHEN ABS(COALESCE(oz_qty,0))>1e-9 THEN 1 ELSE 0 END) nonzero
               FROM recipes WHERE product_id=?""",(pid,))
    winv=one("""SELECT COUNT(*) rows,
                       SUM(CASE WHEN ABS(COALESCE(qty_base,0))>1e-9 OR ABS(COALESCE(qty_bottle_equiv,0))>1e-9 THEN 1 ELSE 0 END) nonzero
                FROM weekly_inventory_counts WHERE product_id=?""",(pid,))
    wsp=one("SELECT COUNT(*) rows FROM weekly_inventory_session_products WHERE product_id=?",(pid,))
    out={
        'inventory_rows':int(inv['rows'] or 0),'inventory_nonzero':int(inv['nonzero'] or 0),
        'weekly_inventory_rows':int(winv['rows'] or 0),'weekly_inventory_nonzero':int(winv['nonzero'] or 0),
        'weekly_session_refs':int(wsp['rows'] or 0),
        'movement_rows':int(mov['rows'] or 0),'movement_nonzero':int(mov['nonzero'] or 0),
        'pos_rows':int(pos['rows'] or 0),'pos_nonzero':int(pos['nonzero'] or 0),
        'recipe_rows':int(rec['rows'] or 0),'recipe_nonzero':int(rec['nonzero'] or 0),
    }
    out['total_rows']=out['inventory_rows']+out['weekly_inventory_rows']+out['weekly_session_refs']+out['movement_rows']+out['pos_rows']+out['recipe_rows']
    out['nonzero_rows']=out['inventory_nonzero']+out['weekly_inventory_nonzero']+out['movement_nonzero']+out['pos_nonzero']+out['recipe_nonzero']
    out['safe_delete_unused']=out['total_rows']==0
    # A duplicate that only generated zero-valued inventory/movement/POS rows and
    # is not used in any recipe can be cleaned without losing physical or sales quantities.
    out['safe_delete_zero_only']=(
        out['total_rows']>0 and out['inventory_nonzero']==0 and out['weekly_inventory_nonzero']==0
        and out['movement_nonzero']==0 and out['pos_nonzero']==0 and out['recipe_rows']==0
        and out['weekly_session_refs']==0
    )
    return out

def _audit_product_admin(action,source,target,user_id,details=''):
    con.execute("""INSERT INTO product_admin_audit(action,source_product_id,source_name,target_product_id,target_name,user_id,created_at,details)
                   VALUES(?,?,?,?,?,?,?,?)""",(
        action, int(source['id']) if source else None, source['name'] if source else None,
        int(target['id']) if target else None, target['name'] if target else None,
        int(user_id) if user_id else None, now_iso(), details or ''
    ))

def delete_product_safely(pid,user_id,allow_zero_references=False):
    """Delete a duplicate only when doing so cannot remove a non-zero business quantity.

    - No references at all: direct delete.
    - Only zero-valued inventory/movement/POS references and no recipes: those zero rows
      may be removed together with the duplicate when explicitly requested by Developer/Owner.
    """
    source=one("SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.id=?",(int(pid),))
    if not source: return False,'Producto no encontrado.'
    usage=product_usage_summary(pid)
    if not usage['safe_delete_unused'] and not (allow_zero_references and usage['safe_delete_zero_only']):
        return False,'El producto tiene información relacionada con valor o una receta; no puede borrarse directamente.'
    try:
        con.execute('BEGIN IMMEDIATE')
        if usage['safe_delete_zero_only']:
            con.execute("DELETE FROM inventory_counts WHERE product_id=? AND ABS(COALESCE(qty_base,0))<=1e-9 AND ABS(COALESCE(qty_bottle_equiv,0))<=1e-9",(int(pid),))
            con.execute("DELETE FROM movements WHERE product_id=? AND ABS(COALESCE(qty_base,0))<=1e-9 AND ABS(COALESCE(qty_bottle_equiv,0))<=1e-9",(int(pid),))
            con.execute("DELETE FROM pos_sales WHERE product_id=? AND ABS(COALESCE(quantity,0))<=1e-9",(int(pid),))
        _audit_product_admin('DELETE_ZERO_ONLY' if usage['safe_delete_zero_only'] else 'DELETE_UNUSED',source,None,user_id,json.dumps(usage,ensure_ascii=False))
        con.execute('DELETE FROM products WHERE id=?',(int(pid),))
        con.commit()
        backup_db(force=True)
        return True,'Producto eliminado de forma segura.'
    except Exception as e:
        con.rollback()
        return False,f'No se pudo eliminar el producto: {e}'

def product_merge_conflicts(source_pid,target_pid):
    """Return collisions that need explicit protection before merging two catalog rows."""
    source_pid,target_pid=int(source_pid),int(target_pid)
    inv=q("""SELECT s.session_date,ic1.session_id,ic1.location_id,ic1.qty_base source_qty,ic1.qty_bottle_equiv source_beq,
                    ic2.qty_base target_qty,ic2.qty_bottle_equiv target_beq
             FROM inventory_counts ic1 JOIN inventory_counts ic2
               ON ic2.session_id=ic1.session_id AND ic2.location_id=ic1.location_id AND ic2.product_id=?
             JOIN inventory_sessions s ON s.id=ic1.session_id
             WHERE ic1.product_id=?""",(target_pid,source_pid))
    unsafe_inv=[r for r in inv if abs(float(r['source_qty'] or 0))>1e-9 or abs(float(r['source_beq'] or 0))>1e-9]
    rec=q("""SELECT c.name cocktail,r1.oz_qty source_oz,r2.oz_qty target_oz
             FROM recipes r1 JOIN recipes r2 ON r2.cocktail_id=r1.cocktail_id AND r2.product_id=?
             JOIN cocktails c ON c.id=r1.cocktail_id WHERE r1.product_id=?""",(target_pid,source_pid))
    unsafe_rec=[r for r in rec if abs(float(r['source_oz'] or 0))>1e-9]
    return {'inventory_collisions':inv,'unsafe_inventory':unsafe_inv,'recipe_collisions':rec,'unsafe_recipes':unsafe_rec}

def merge_duplicate_product(source_pid,target_pid,user_id):
    """Move references to the correct product and retire the duplicate atomically.

    Non-zero same-session inventory collisions and duplicate recipe ingredients are blocked
    because automatically summing them could change historical meaning. Zero collisions are
    safely discarded as duplicate placeholders.
    """
    source=one("SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.id=?",(int(source_pid),))
    target=one("SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.id=?",(int(target_pid),))
    if not source or not target or int(source_pid)==int(target_pid): return False,'Selecciona dos productos diferentes.'
    if source['category']!=target['category']: return False,'Solo se pueden fusionar productos de la misma categoría.'
    sm=float(source['bottle_ml'] or 0); tm=float(target['bottle_ml'] or 0)
    if sm>0 and tm>0 and abs(sm-tm)>1e-6:
        return False,'Las presentaciones en ml son diferentes. No se fusionan automáticamente para no reinterpretar botellas históricas.'
    if str(source['package_type'] or '')!=str(target['package_type'] or ''):
        return False,'Los tipos de envase son diferentes. Revisa el catálogo antes de fusionar.'
    conflicts=product_merge_conflicts(source_pid,target_pid)
    if conflicts['unsafe_inventory']:
        return False,'Hay sesiones donde ambos productos tienen conteos no cero. La fusión automática está bloqueada para no duplicar o sumar inventario histórico.'
    if conflicts['unsafe_recipes']:
        return False,'Ambos productos aparecen en la misma receta con cantidades. Revisa esa receta antes de fusionar.'
    usage_before=product_usage_summary(source_pid)
    if usage_before.get('weekly_session_refs',0)>0:
        return False,'El producto ya forma parte de un inventario semanal. Para preservar la fotografía histórica, desactívalo en lugar de fusionarlo.'
    try:
        con.execute('BEGIN IMMEDIATE')
        # Remove only zero-valued source rows that collide with an existing target row.
        con.execute("""DELETE FROM inventory_counts
                     WHERE product_id=? AND ABS(COALESCE(qty_base,0))<=1e-9 AND ABS(COALESCE(qty_bottle_equiv,0))<=1e-9
                       AND EXISTS(SELECT 1 FROM inventory_counts t WHERE t.product_id=?
                                  AND t.session_id=inventory_counts.session_id AND t.location_id=inventory_counts.location_id)""",(int(source_pid),int(target_pid)))
        # A zero recipe collision is safe to drop; non-zero collisions were blocked above.
        con.execute("""DELETE FROM recipes WHERE product_id=? AND ABS(COALESCE(oz_qty,0))<=1e-9
                     AND EXISTS(SELECT 1 FROM recipes t WHERE t.product_id=? AND t.cocktail_id=recipes.cocktail_id)""",(int(source_pid),int(target_pid)))
        con.execute('UPDATE inventory_counts SET product_id=? WHERE product_id=?',(int(target_pid),int(source_pid)))
        con.execute('UPDATE movements SET product_id=? WHERE product_id=?',(int(target_pid),int(source_pid)))
        con.execute('UPDATE pos_sales SET product_id=? WHERE product_id=?',(int(target_pid),int(source_pid)))
        con.execute('UPDATE recipes SET product_id=? WHERE product_id=?',(int(target_pid),int(source_pid)))
        if int(source['daily_inventory'] or 0)==1:
            con.execute('UPDATE products SET daily_inventory=1 WHERE id=?',(int(target_pid),))
        _audit_product_admin('MERGE_DUPLICATE',source,target,user_id,json.dumps(usage_before,ensure_ascii=False))
        con.execute('DELETE FROM products WHERE id=?',(int(source_pid),))
        con.commit()
        backup_db(force=True)
        return True,f"{source['name']} fue fusionado con {target['name']} y el duplicado fue retirado."
    except Exception as e:
        con.rollback()
        return False,f'No se pudo fusionar el producto: {e}'

def unit_label(p): return "botellas" if p['category']=="Cerveza" else "oz"

def qty_fmt(p, v):
    if v is None: return "—"
    return f"{v:.0f} botellas" if p['category']=="Cerveza" else f"{v:.2f} oz"

def last_close(pid, lid, before_or_on=None):
    sql="""SELECT ic.qty_base,s.session_date,s.created_at FROM inventory_counts ic
           JOIN inventory_sessions s ON s.id=ic.session_id
           WHERE ic.product_id=? AND ic.location_id=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'"""
    ps=[pid,lid]
    if before_or_on: sql += " AND s.session_date<=?"; ps.append(before_or_on)
    sql += " ORDER BY s.session_date DESC,s.created_at DESC LIMIT 1"
    r=one(sql,ps); return (float(r['qty_base']),r['session_date']) if r else (None,None)

def _normalized_count_signature(counts):
    """Stable signature used only to suppress accidental immediate re-submits."""
    rows=[]
    for x in counts:
        beq=x.get('bottle_equiv')
        rows.append((int(x['pid']),int(x['lid']),round(float(x.get('qty') or 0),6),None if beq is None else round(float(beq),6)))
    return tuple(sorted(rows))


def _recent_identical_inventory_session(kind, counts, session_date, inventory_cycle, paired_opening_session_id=None, max_age_seconds=120):
    """Find an identical session recently saved by the same user.

    This is a defensive idempotency guard for double taps, browser retries and
    Streamlit reruns. The short window avoids blocking a legitimate later recount.
    """
    d=session_date.isoformat() if hasattr(session_date,'isoformat') else str(session_date)
    now_utc=datetime.now(timezone.utc).replace(tzinfo=None)
    candidates=q("""SELECT id,created_at,paired_opening_session_id FROM inventory_sessions
                    WHERE session_date=? AND session_type=? AND user_id=?
                      AND COALESCE(inventory_cycle,'DAILY')=?
                    ORDER BY created_at DESC,id DESC LIMIT 6""",
                 (d,kind,user['id'],inventory_cycle))
    target=_normalized_count_signature(counts)
    for r in candidates:
        try:
            created=datetime.fromisoformat(str(r['created_at']))
            if created.tzinfo is not None:
                created=created.astimezone(timezone.utc).replace(tzinfo=None)
            if (now_utc-created).total_seconds()>max_age_seconds:
                continue
        except Exception:
            continue
        paired=r['paired_opening_session_id'] if 'paired_opening_session_id' in r.keys() else None
        if (paired or None)!=(paired_opening_session_id or None):
            continue
        saved=q("""SELECT product_id,location_id,qty_base,qty_bottle_equiv
                   FROM inventory_counts WHERE session_id=? ORDER BY product_id,location_id,id""",(r['id'],))
        saved_sig=tuple(sorted((int(x['product_id']),int(x['location_id']),round(float(x['qty_base'] or 0),6),None if x['qty_bottle_equiv'] is None else round(float(x['qty_bottle_equiv']),6)) for x in saved))
        if saved_sig==target:
            return r
    return None


def _confirmed_backup_after_write():
    """Require a confirmed durable backup after a committed business write.

    A second full attempt is made because the local transaction is already committed; subsequent
    writes will be blocked by _write_sync_guard until this local descendant is published.
    """
    ok,msg=backup_db()
    if ok:return ok,msg
    time.sleep(0.8)
    return backup_db(force=True)


@_serialized_durable_write
def save_session(kind, counts, session_date=None, notes="", inventory_cycle="DAILY", paired_opening_session_id=None, pending_movements=None):
    """Save one immutable inventory capture with transaction + duplicate protection.

    Inventory session, all product counts and any movements entered as part of a
    closing are committed atomically. An identical submission by the same user
    within two minutes is treated as a retry and is not inserted again.
    """
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:
        return {'ok':False,'saved':False,'duplicate':False,'error':guard_msg}
    if SYNC_PREFLIGHT_STATUS.get('status')=='conflict':
        return {'ok':False,'saved':False,'duplicate':False,'error':'Sincronización en conflicto. La captura fue bloqueada para evitar pérdida de datos. Contacta al Developer/Owner.'}
    business_date=(session_date or local_today())
    d=business_date.isoformat() if hasattr(business_date,'isoformat') else str(business_date)
    pending_movements=pending_movements or []

    duplicate=_recent_identical_inventory_session(kind,counts,business_date,inventory_cycle,paired_opening_session_id)
    if duplicate:
        return {'ok':True,'saved':False,'duplicate':True,'id':int(duplicate['id']),'created_at':duplicate['created_at']}

    created_at=now_iso()
    try:
        con.execute("BEGIN IMMEDIATE")
        # Recheck after the write lock so concurrent users cannot slip a second
        # session between validation and insert.
        duplicate=_recent_identical_inventory_session(kind,counts,business_date,inventory_cycle,paired_opening_session_id)
        if duplicate:
            con.rollback()
            return {'ok':True,'saved':False,'duplicate':True,'id':int(duplicate['id']),'created_at':duplicate['created_at']}

        valid,msg=_validate_inventory_save(kind,business_date,inventory_cycle)
        if not valid:
            con.rollback()
            return {'ok':False,'saved':False,'duplicate':False,'error':msg}

        cur=con.execute("""INSERT INTO inventory_sessions(session_date,session_type,user_id,created_at,notes,inventory_cycle,paired_opening_session_id)
                           VALUES(?,?,?,?,?,?,?)""",
                        (d,kind,user['id'],created_at,notes,inventory_cycle,paired_opening_session_id))
        sid=cur.lastrowid
        for x in counts:
            con.execute("""INSERT INTO inventory_counts(session_id,product_id,location_id,qty_base,previous_qty,variance,observation,qty_bottle_equiv)
                           VALUES(?,?,?,?,?,?,?,?)""",
                        (sid,x['pid'],x['lid'],x['qty'],x.get('prev'),x.get('var'),x.get('obs'),x.get('bottle_equiv')))

        for typ,pid,qty,beq,fr,to,sup,ref,obs in pending_movements:
            con.execute("""INSERT INTO movements(movement_date,movement_type,product_id,qty_base,from_location_id,to_location_id,user_id,supplier,reference,observation,created_at,qty_bottle_equiv)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (d,typ,pid,qty,fr,to,user['id'],sup,ref,obs,created_at,beq))
        con.commit()
    except Exception:
        con.rollback()
        raise
    backup_ok,backup_msg=_confirmed_backup_after_write()
    return {'ok':True,'saved':True,'duplicate':False,'id':int(sid),'created_at':created_at,'backup_ok':backup_ok,'backup_message':backup_msg}

@_serialized_durable_write
def save_daily_closing_capture(counts, operation_date, notes="", pending_movements=None):
    """V0.6.0 live daily close. Historical OPENING rows remain untouched.

    The first partial capture freezes the required product set and the previous closing
    boundary in a marker stored inside the immutable session notes. Every later partial
    capture reuses that same marker, so the physical comparison always points to the same
    prior close even when users count beer and liquor at different times.
    """
    marker,meta=_close_cycle_marker_for_save(operation_date)
    enriched=[]
    for x in counts:
        y=dict(x)
        prev=_baseline_count_before_id(y['pid'],y['lid'],meta.get('baseid',0))
        if prev is not None:
            if y.get('category')=='Licor' and y.get('bottle_equiv') is not None and prev['qty_bottle_equiv'] is not None:
                y['prev']=float(prev['qty_base'] or 0)
                y['var']=float(y.get('qty') or 0)-float(prev['qty_base'] or 0)
            else:
                y['prev']=float(prev['qty_base'] or 0)
                y['var']=float(y.get('qty') or 0)-float(prev['qty_base'] or 0)
        enriched.append(y)
    full_notes=marker + (("\n"+str(notes).strip()) if str(notes or '').strip() else '')
    return save_session('CLOSING',enriched,operation_date,full_notes,inventory_cycle='DAILY',paired_opening_session_id=None,pending_movements=pending_movements or [])


@_serialized_durable_write
def save_historical_session(kind, counts, session_date, notes="", inventory_cycle="DAILY", paired_opening_session_id=None):
    """Developer/Owner historical capture from paper records.

    This intentionally bypasses the live Opening→Closing workflow because it edits an
    earlier business date. The real entry timestamp and Developer user are preserved.
    """
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:
        return {'ok':False,'saved':False,'duplicate':False,'error':guard_msg}
    if SYNC_PREFLIGHT_STATUS.get('status')=='conflict':
        return {'ok':False,'saved':False,'duplicate':False,'error':'Sincronización en conflicto. La carga histórica fue bloqueada para proteger los datos.'}
    d=session_date.isoformat() if hasattr(session_date,'isoformat') else str(session_date)
    duplicate=_recent_identical_inventory_session(kind,counts,session_date,inventory_cycle,paired_opening_session_id)
    if duplicate:
        return {'ok':True,'saved':False,'duplicate':True,'id':int(duplicate['id']),'created_at':duplicate['created_at']}
    created_at=now_iso()
    try:
        con.execute('BEGIN IMMEDIATE')
        duplicate=_recent_identical_inventory_session(kind,counts,session_date,inventory_cycle,paired_opening_session_id)
        if duplicate:
            con.rollback()
            return {'ok':True,'saved':False,'duplicate':True,'id':int(duplicate['id']),'created_at':duplicate['created_at']}
        cur=con.execute("""INSERT INTO inventory_sessions(session_date,session_type,user_id,created_at,notes,inventory_cycle,paired_opening_session_id)
                           VALUES(?,?,?,?,?,?,?)""",
                        (d,kind,user['id'],created_at,notes,inventory_cycle,paired_opening_session_id))
        sid=cur.lastrowid
        for x in counts:
            con.execute("""INSERT INTO inventory_counts(session_id,product_id,location_id,qty_base,previous_qty,variance,observation,qty_bottle_equiv)
                           VALUES(?,?,?,?,?,?,?,?)""",
                        (sid,x['pid'],x['lid'],x['qty'],x.get('prev'),x.get('var'),x.get('obs'),x.get('bottle_equiv')))
        con.commit()
    except Exception:
        con.rollback(); raise
    backup_ok,backup_msg=_confirmed_backup_after_write()
    return {'ok':True,'saved':True,'duplicate':False,'id':int(sid),'created_at':created_at,'backup_ok':backup_ok,'backup_message':backup_msg}


# ---------------------- V0.5.9 independent weekly inventory ----------------------
def weekly_active_session():
    return one("""SELECT w.*,u.name started_by
                  FROM weekly_inventory_sessions w
                  LEFT JOIN users u ON u.id=w.started_by_user_id
                  WHERE w.status='IN_PROGRESS'
                  ORDER BY w.started_at DESC,w.id DESC LIMIT 1""")


def weekly_session_by_id(session_id):
    return one("""SELECT w.*,u.name started_by,cu.name completed_by
                  FROM weekly_inventory_sessions w
                  LEFT JOIN users u ON u.id=w.started_by_user_id
                  LEFT JOIN users cu ON cu.id=w.completed_by_user_id
                  WHERE w.id=?""",(int(session_id),))


def weekly_session_products(session_id):
    return q("""SELECT p.*,c.name category,c.count_unit
                FROM weekly_inventory_session_products wsp
                JOIN products p ON p.id=wsp.product_id
                JOIN categories c ON c.id=p.category_id
                WHERE wsp.weekly_session_id=?
                ORDER BY c.name,p.name,COALESCE(p.bottle_ml,0)""",(int(session_id),))


def weekly_latest_count(session_id,pid,location_id):
    return one("""SELECT wc.*,u.name employee
                  FROM weekly_inventory_counts wc
                  LEFT JOIN users u ON u.id=wc.user_id
                  WHERE wc.weekly_session_id=? AND wc.product_id=? AND wc.location_id=?
                  ORDER BY wc.created_at DESC,wc.id DESC LIMIT 1""",
               (int(session_id),int(pid),int(location_id)))


def weekly_inventory_progress(session_id):
    required={int(r['product_id']) for r in q("SELECT product_id FROM weekly_inventory_session_products WHERE weekly_session_id=?",(int(session_id),))}
    counted={int(r['product_id']) for r in q("SELECT DISTINCT product_id FROM weekly_inventory_counts WHERE weekly_session_id=?",(int(session_id),))}
    return {
        'required_ids':required,'counted_ids':counted,'required_count':len(required),
        'counted_count':len(required & counted),'complete':bool(required) and required.issubset(counted),
        'pending_ids':required-counted,
    }


def weekly_last_completed_count(pid,location_id,before_or_on=None):
    sql="""SELECT wc.qty_base,wc.qty_bottle_equiv,w.inventory_date,w.completed_at,w.id weekly_session_id
             FROM weekly_inventory_counts wc
             JOIN weekly_inventory_sessions w ON w.id=wc.weekly_session_id
             WHERE wc.product_id=? AND wc.location_id=? AND w.status='COMPLETED'"""
    ps=[int(pid),int(location_id)]
    if before_or_on:
        sql += " AND w.inventory_date<=?"; ps.append(str(before_or_on))
    sql += " ORDER BY w.inventory_date DESC,w.completed_at DESC,w.id DESC,wc.created_at DESC,wc.id DESC LIMIT 1"
    return one(sql,ps)


@_serialized_durable_write
def start_weekly_inventory(inventory_date,notes=''):
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:return {'ok':False,'error':guard_msg}
    d=inventory_date.isoformat() if hasattr(inventory_date,'isoformat') else str(inventory_date)
    if date.fromisoformat(d)>local_today():return {'ok':False,'error':'La fecha del inventario semanal no puede estar en el futuro.'}
    existing=weekly_active_session()
    if existing:return {'ok':True,'existing':True,'id':int(existing['id']),'created_at':existing['started_at']}
    same_day=one("SELECT id FROM weekly_inventory_sessions WHERE inventory_date=? AND status='COMPLETED' ORDER BY completed_at DESC LIMIT 1",(d,))
    if same_day:return {'ok':False,'error':'Ya existe un inventario semanal finalizado para esa fecha. Para preservar trazabilidad no se crea un segundo inventario semanal del mismo día.'}
    physical=[p for p in products() if p['category'] in ('Cerveza','Licor')]
    if not physical:return {'ok':False,'error':'No hay productos físicos activos para inventariar.'}
    created=now_iso()
    try:
        con.execute('BEGIN IMMEDIATE')
        # Re-check while holding the SQLite write lock.
        r=con.execute("SELECT id,started_at FROM weekly_inventory_sessions WHERE status='IN_PROGRESS' ORDER BY started_at DESC,id DESC LIMIT 1").fetchone()
        if r:
            con.rollback();return {'ok':True,'existing':True,'id':int(r['id']),'created_at':r['started_at']}
        cur=con.execute("""INSERT INTO weekly_inventory_sessions(inventory_date,status,started_by_user_id,started_at,notes)
                           VALUES(?,'IN_PROGRESS',?,?,?)""",(d,user['id'],created,notes or ''))
        sid=int(cur.lastrowid)
        con.executemany("INSERT INTO weekly_inventory_session_products(weekly_session_id,product_id) VALUES(?,?)",[(sid,int(p['id'])) for p in physical])
        con.commit()
    except Exception as exc:
        con.rollback();return {'ok':False,'error':str(exc)}
    bok,bmsg=_confirmed_backup_after_write()
    return {'ok':True,'existing':False,'id':sid,'created_at':created,'backup_ok':bok,'backup_message':bmsg}


def _weekly_capture_signature(counts):
    rows=[]
    for x in counts:
        beq=x.get('bottle_equiv')
        rows.append((int(x['pid']),int(x['lid']),round(float(x.get('qty') or 0),6),None if beq is None else round(float(beq),6)))
    return tuple(sorted(rows))


def _recent_identical_weekly_capture(session_id,counts,max_age_seconds=120):
    target=_weekly_capture_signature(counts)
    now_utc=datetime.now(timezone.utc).replace(tzinfo=None)
    captures=q("""SELECT id,created_at FROM weekly_inventory_captures
                  WHERE weekly_session_id=? AND user_id=? ORDER BY created_at DESC,id DESC LIMIT 5""",
               (int(session_id),user['id']))
    for cap in captures:
        try:
            created=datetime.fromisoformat(str(cap['created_at']))
            if created.tzinfo is not None:created=created.astimezone(timezone.utc).replace(tzinfo=None)
            if (now_utc-created).total_seconds()>max_age_seconds:continue
        except Exception:continue
        rows=q("""SELECT product_id,location_id,qty_base,qty_bottle_equiv
                  FROM weekly_inventory_counts WHERE capture_id=? ORDER BY product_id,location_id,id""",(cap['id'],))
        sig=tuple(sorted((int(r['product_id']),int(r['location_id']),round(float(r['qty_base'] or 0),6),None if r['qty_bottle_equiv'] is None else round(float(r['qty_bottle_equiv']),6)) for r in rows))
        if sig==target:return cap
    return None


@_serialized_durable_write
def save_weekly_inventory_progress(session_id,counts,scope='Todo el inventario',observation=''):
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:return {'ok':False,'saved':False,'error':guard_msg}
    session=weekly_session_by_id(session_id)
    if not session or session['status']!='IN_PROGRESS':return {'ok':False,'saved':False,'error':'El inventario semanal ya no está activo.'}
    allowed={int(r['product_id']) for r in q("SELECT product_id FROM weekly_inventory_session_products WHERE weekly_session_id=?",(int(session_id),))}
    clean=[x for x in counts if int(x['pid']) in allowed]
    if not clean:return {'ok':False,'saved':False,'error':'No hay productos válidos para guardar en esta captura.'}
    duplicate=_recent_identical_weekly_capture(session_id,clean)
    if duplicate:return {'ok':True,'saved':False,'duplicate':True,'created_at':duplicate['created_at'],'capture_id':int(duplicate['id']),'backup_ok':True}
    created=now_iso()
    try:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute("SELECT status FROM weekly_inventory_sessions WHERE id=?",(int(session_id),)).fetchone()
        if not row or row['status']!='IN_PROGRESS':
            con.rollback();return {'ok':False,'saved':False,'error':'El inventario semanal fue finalizado por otro usuario. Actualiza la página.'}
        # Optimistic per-product concurrency guard: if another user counted one of these products
        # after this form was rendered, do not silently overwrite their newer physical count.
        for x in clean:
            latest=con.execute("""SELECT id FROM weekly_inventory_counts
                                  WHERE weekly_session_id=? AND product_id=? AND location_id=?
                                  ORDER BY created_at DESC,id DESC LIMIT 1""",
                               (int(session_id),int(x['pid']),int(x['lid']))).fetchone()
            actual=(int(latest['id']) if latest else None)
            expected=x.get('expected_count_id')
            expected=(int(expected) if expected is not None else None)
            if actual!=expected:
                con.rollback();return {'ok':False,'saved':False,'error':f"{x.get('name','Un producto')} fue actualizado por otro usuario mientras tenías esta pantalla abierta. Actualiza la página y vuelve a contar ese producto para evitar sobrescribir información."}
        duplicate=_recent_identical_weekly_capture(session_id,clean)
        if duplicate:
            con.rollback();return {'ok':True,'saved':False,'duplicate':True,'created_at':duplicate['created_at'],'capture_id':int(duplicate['id']),'backup_ok':True}
        cur=con.execute("""INSERT INTO weekly_inventory_captures(weekly_session_id,user_id,created_at,scope,observation)
                           VALUES(?,?,?,?,?)""",(int(session_id),user['id'],created,scope,observation or ''))
        capture_id=int(cur.lastrowid)
        for x in clean:
            con.execute("""INSERT INTO weekly_inventory_counts(capture_id,weekly_session_id,product_id,location_id,qty_base,qty_bottle_equiv,observation,user_id,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?)""",
                        (capture_id,int(session_id),int(x['pid']),int(x['lid']),float(x.get('qty') or 0),x.get('bottle_equiv'),x.get('obs',''),user['id'],created))
        con.commit()
    except Exception as exc:
        con.rollback();return {'ok':False,'saved':False,'error':str(exc)}
    bok,bmsg=_confirmed_backup_after_write()
    return {'ok':True,'saved':True,'duplicate':False,'created_at':created,'capture_id':capture_id,'backup_ok':bok,'backup_message':bmsg}


@_serialized_durable_write
def complete_weekly_inventory(session_id,notes=''):
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:return {'ok':False,'error':guard_msg}
    prog=weekly_inventory_progress(session_id)
    if not prog['complete']:
        return {'ok':False,'error':f"Faltan {prog['required_count']-prog['counted_count']} productos por contar antes de finalizar."}
    completed=now_iso()
    try:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute("SELECT status,notes FROM weekly_inventory_sessions WHERE id=?",(int(session_id),)).fetchone()
        if not row:
            con.rollback();return {'ok':False,'error':'Inventario semanal no encontrado.'}
        if row['status']=='COMPLETED':
            con.rollback();return {'ok':True,'already_completed':True,'created_at':completed,'backup_ok':True}
        final_notes=(str(row['notes'] or '') + ('\n' if row['notes'] and notes else '') + str(notes or '')).strip()
        con.execute("""UPDATE weekly_inventory_sessions
                       SET status='COMPLETED',completed_by_user_id=?,completed_at=?,notes=? WHERE id=?""",
                    (user['id'],completed,final_notes,int(session_id)))
        con.commit()
    except Exception as exc:
        con.rollback();return {'ok':False,'error':str(exc)}
    bok,bmsg=_confirmed_backup_after_write()
    return {'ok':True,'already_completed':False,'created_at':completed,'backup_ok':bok,'backup_message':bmsg}


def weekly_recent_sessions(limit=8):
    return q("""SELECT w.*,u.name started_by,cu.name completed_by,
                     (SELECT COUNT(*) FROM weekly_inventory_session_products sp WHERE sp.weekly_session_id=w.id) required_count,
                     (SELECT COUNT(DISTINCT wc.product_id) FROM weekly_inventory_counts wc WHERE wc.weekly_session_id=w.id) counted_count
                FROM weekly_inventory_sessions w
                LEFT JOIN users u ON u.id=w.started_by_user_id
                LEFT JOIN users cu ON cu.id=w.completed_by_user_id
                ORDER BY w.inventory_date DESC,w.started_at DESC,w.id DESC LIMIT ?""",(int(limit),))


def bottle_count_input(p, key, default_base=0.0, default_bottles=None):
    if p['category']=='Cerveza':
        units=float(st.number_input("Unidades / botellas",min_value=0,value=int(round(max(float(default_base or 0),0))),step=1,key=key+'u'))
        return {'base':units,'bottles':None}
    boz=bottle_oz(p)
    if default_bottles is None:
        default_bottles=(max(float(default_base or 0),0)/boz) if boz else 0.0
    default_bottles=max(float(default_bottles or 0),0)
    full=int(math.floor(default_bottles+1e-9)); frac_raw=max(0.0,min(default_bottles-full,.99))
    fractions=[0.0,0.25,0.50,0.75]; frac=min(fractions,key=lambda x:abs(x-frac_raw))
    c1,c2=st.columns([1.2,1])
    full_val=int(c1.number_input("Botellas completas",min_value=0,value=full,step=1,key=key+'f'))
    frac_val=float(c2.selectbox("Fracción botella abierta",fractions,index=fractions.index(frac),format_func=lambda x:{0.0:'0 (sin abierta)',0.25:'0.25 · ¼',0.5:'0.50 · ½',0.75:'0.75 · ¾'}[x],key=key+'q'))
    bottle_equiv=full_val+frac_val
    if boz:
        total_oz=bottle_equiv*boz
        st.caption(f"Conteo: {bottle_equiv:.2f} botellas · {p['bottle_ml']:.0f} ml/botella · Total calculado: {total_oz:.2f} oz")
        return {'base':total_oz,'bottles':bottle_equiv}
    st.info(f"Conteo guardado: {bottle_equiv:.2f} botellas. La presentación en ml está pendiente; las oz se calcularán automáticamente cuando el ADMIN registre los ml.")
    return {'base':0.0,'bottles':bottle_equiv}

def last_close_detail(pid,lid,before_or_on=None):
    sql="""SELECT ic.qty_base,ic.qty_bottle_equiv,s.session_date,s.created_at FROM inventory_counts ic
           JOIN inventory_sessions s ON s.id=ic.session_id
           WHERE ic.product_id=? AND ic.location_id=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'"""
    ps=[pid,lid]
    if before_or_on: sql += " AND s.session_date<=?"; ps.append(before_or_on)
    sql += " ORDER BY s.session_date DESC,s.created_at DESC LIMIT 1"
    r=one(sql,ps)
    return (float(r['qty_base']), float(r['qty_bottle_equiv']) if r['qty_bottle_equiv'] is not None else None, r['session_date']) if r else (None,None,None)

def session_qty_detail(d,pid,kind,lid):
    r=one("""SELECT ic.qty_base,ic.qty_bottle_equiv FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             WHERE s.session_date=? AND s.session_type=? AND ic.product_id=? AND ic.location_id=?
             ORDER BY s.created_at DESC LIMIT 1""",(d,kind,pid,lid))
    return (float(r['qty_base']), float(r['qty_bottle_equiv']) if r['qty_bottle_equiv'] is not None else None) if r else (None,None)

def backfill_product_bottle_counts(pid):
    p=one("SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.id=?",(pid,))
    if not p or p['category']!='Licor' or not p['bottle_ml']:
        return
    boz=float(p['bottle_ml'])/ML_PER_OZ
    con.execute("UPDATE inventory_counts SET qty_base=qty_bottle_equiv*? WHERE product_id=? AND qty_bottle_equiv IS NOT NULL",(boz,pid))
    con.execute("UPDATE weekly_inventory_counts SET qty_base=qty_bottle_equiv*? WHERE product_id=? AND qty_bottle_equiv IS NOT NULL",(boz,pid))
    con.execute("UPDATE movements SET qty_base=qty_bottle_equiv*? WHERE product_id=? AND qty_bottle_equiv IS NOT NULL",(boz,pid))
    con.commit(); backup_db()

def movement_qty_input(p,key,label="Cantidad"):
    if p['category']=='Cerveza':
        units=float(st.number_input(f"{label} · unidades / botellas",min_value=0,value=0,step=1,key=key+'u'))
        return {'base':units,'bottles':None}
    fractions=[0.0,0.25,0.50,0.75]
    c1,c2=st.columns([1.2,1])
    full=int(c1.number_input(f"{label} · botellas completas",min_value=0,value=0,step=1,key=key+'f'))
    frac=float(c2.selectbox("Fracción botella abierta",fractions,index=0,format_func=lambda x:{0.0:'0 (sin abierta)',0.25:'0.25 · ¼',0.5:'0.50 · ½',0.75:'0.75 · ¾'}[x],key=key+'q'))
    bottles=full+frac; boz=bottle_oz(p)
    if boz:
        base=bottles*boz; st.caption(f"Movimiento: {bottles:.2f} botellas · {p['bottle_ml']:.0f} ml/botella · {base:.2f} oz")
    else:
        base=0.0
        if bottles>0: st.caption(f"Movimiento: {bottles:.2f} botellas · ml pendiente; se convertirán a oz cuando se complete la presentación.")
    return {'base':base,'bottles':bottles}

@_serialized_durable_write
def create_movement(typ,pid,qty,from_id=None,to_id=None,supplier=None,reference=None,obs="",d=None,bottle_equiv=None,do_backup=True):
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:
        raise RuntimeError(guard_msg)
    if SYNC_PREFLIGHT_STATUS.get('status')=='conflict':
        raise RuntimeError('Sincronización en conflicto. Movimiento bloqueado para evitar pérdida de datos.')
    con.execute("""INSERT INTO movements(movement_date,movement_type,product_id,qty_base,from_location_id,to_location_id,user_id,supplier,reference,observation,created_at,qty_bottle_equiv)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",((d or local_today()).isoformat(),typ,pid,qty,from_id,to_id,user['id'],supplier,reference,obs,now_iso(),bottle_equiv))
    con.commit()
    if do_backup:
        ok,msg=_confirmed_backup_after_write()
        if not ok: raise RuntimeError('Movimiento guardado localmente, pero el respaldo durable quedó pendiente: '+msg)


@_serialized_durable_write
def save_movements_batch(entries):
    """Atomically save a group of supplier/transfer movements, then confirm one durable backup."""
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:return {'ok':False,'error':guard_msg}
    created=now_iso()
    try:
        con.execute('BEGIN IMMEDIATE')
        for e in entries:
            con.execute("""INSERT INTO movements(movement_date,movement_type,product_id,qty_base,from_location_id,to_location_id,user_id,supplier,reference,observation,created_at,qty_bottle_equiv)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (e['date'],e['type'],e['pid'],e['qty'],e.get('from_id'),e.get('to_id'),user['id'],e.get('supplier'),e.get('reference'),e.get('obs',''),created,e.get('bottle_equiv')))
        con.commit()
    except Exception as exc:
        con.rollback();return {'ok':False,'error':str(exc)}
    bok,bmsg=_confirmed_backup_after_write()
    return {'ok':True,'backup_ok':bok,'backup_message':bmsg,'created_at':created}

def session_qty(d, pid, kind, lid):
    r=one("""SELECT ic.qty_base FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             WHERE s.session_date=? AND s.session_type=? AND ic.product_id=? AND ic.location_id=?
             ORDER BY s.created_at DESC LIMIT 1""",(d,kind,pid,lid))
    return float(r['qty_base']) if r else None

# ---------------------- V0.4.8 session-safe reconciliation ----------------------
def _inventory_session(ds, kind, cycle=None, before_created_at=None):
    """Latest immutable session matching date/type/cycle.

    before_created_at is used to ensure a closing can only be paired to an opening
    that existed before that closing was saved.
    """
    sql="""SELECT s.*,u.name employee,COUNT(ic.id) item_count
             FROM inventory_sessions s
             LEFT JOIN users u ON u.id=s.user_id
             LEFT JOIN inventory_counts ic ON ic.session_id=s.id
             WHERE s.session_date=? AND s.session_type=?"""
    ps=[ds,kind]
    if cycle:
        sql += " AND COALESCE(s.inventory_cycle,'DAILY')=?"; ps.append(cycle)
    if before_created_at:
        sql += " AND s.created_at<=?"; ps.append(before_created_at)
    sql += " GROUP BY s.id ORDER BY s.created_at DESC,s.id DESC LIMIT 1"
    return one(sql,ps)

def _inventory_session_by_id(session_id):
    if not session_id: return None
    return one("""SELECT s.*,u.name employee,COUNT(ic.id) item_count
                  FROM inventory_sessions s
                  LEFT JOIN users u ON u.id=s.user_id
                  LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                  WHERE s.id=? GROUP BY s.id""",(session_id,))

def _inventory_session_candidates(ds,kind,cycle):
    return q("""SELECT s.*,u.name employee,COUNT(ic.id) item_count
                FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                WHERE s.session_date=? AND s.session_type=? AND COALESCE(s.inventory_cycle,'DAILY')=?
                GROUP BY s.id ORDER BY s.created_at DESC,s.id DESC""",(ds,kind,cycle))

def _paired_inventory_sessions(ds, preferred_cycle=None):
    """Return one coherent opening/closing pair for a business date.

    Priority: latest closing (optionally within preferred_cycle), then its stored
    paired opening. Historical closings without a stored link are paired to the
    latest opening of the SAME cycle saved before the closing. If no closing exists,
    the latest opening determines the active cycle. No cross-cycle mixing occurs.
    """
    # Operational reconciliation is DAILY by default. Legacy WEEKLY Opening/Closing rows
    # remain auditable but never replace the independent weekly snapshot introduced in V0.5.9.
    closing=_inventory_session(ds,'CLOSING',preferred_cycle or 'DAILY')
    if closing:
        cycle=str(closing['inventory_cycle'] or 'DAILY')
        opening=None
        try:
            paired_id=closing['paired_opening_session_id']
        except Exception:
            paired_id=None
        if paired_id:
            candidate=_inventory_session_by_id(paired_id)
            if candidate and candidate['session_date']==ds and candidate['session_type']=='OPENING' and str(candidate['inventory_cycle'] or 'DAILY')==cycle:
                opening=candidate
        if opening is None:
            opening=_inventory_session(ds,'OPENING',cycle,closing['created_at'])
        return opening,closing,cycle
    if preferred_cycle:
        opening=_inventory_session(ds,'OPENING',preferred_cycle)
        if opening: return opening,None,str(opening['inventory_cycle'] or preferred_cycle)
        return None,None,preferred_cycle
    # Before a close exists, prioritize the operational DAILY cycle when present.
    # A later weekly count must not hide a daily opening already in progress.
    opening=_inventory_session(ds,'OPENING','DAILY') or _inventory_session(ds,'OPENING')
    if opening:
        return opening,None,str(opening['inventory_cycle'] or 'DAILY')
    return None,None,'DAILY'

def _count_record_for_session(session_id,pid,lid):
    if not session_id: return None
    return one("""SELECT ic.qty_base,ic.qty_bottle_equiv,ic.previous_qty,ic.variance,COALESCE(ic.observation,'') observation
                  FROM inventory_counts ic WHERE ic.session_id=? AND ic.product_id=? AND ic.location_id=?
                  ORDER BY ic.id DESC LIMIT 1""",(session_id,pid,lid))

def _latest_product_count(ds,pid,kind,lid,cycle,before_created_at=None):
    """Latest count for one product within the SAME date/cycle.

    This is intentionally product-level so beer and liquor counts can be submitted at
    different hours without losing or replacing each other.
    """
    sql="""SELECT ic.qty_base,ic.qty_bottle_equiv,ic.previous_qty,ic.variance,COALESCE(ic.observation,'') observation,
                    s.id session_id,s.created_at,s.inventory_cycle,u.name employee
             FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             LEFT JOIN users u ON u.id=s.user_id
             WHERE s.session_date=? AND s.session_type=? AND ic.product_id=? AND ic.location_id=?
               AND COALESCE(s.inventory_cycle,'DAILY')=?"""
    ps=[ds,kind,pid,lid,cycle]
    if before_created_at:
        sql += " AND s.created_at<=?"; ps.append(before_created_at)
    sql += " ORDER BY s.created_at DESC,s.id DESC,ic.id DESC LIMIT 1"
    return one(sql,ps)

def _count_value_for_reconciliation(p, rec):
    """Return physical value in the best available basis.

    Beer -> units. Liquor with presentation -> oz. Liquor without ml -> bottle equivalents.
    This prevents a valid bottle count from being displayed/calculated as 0 oz.
    """
    if rec is None: return None
    if p['category']=='Cerveza': return float(rec['qty_base'] or 0), 'unit'
    if p['bottle_ml']: return float(rec['qty_base'] or 0), 'oz'
    if rec['qty_bottle_equiv'] is not None: return float(rec['qty_bottle_equiv']), 'bottle'
    # Historical imports before bottle-equivalent storage may already contain oz.
    # Preserve those non-zero values instead of discarding them.
    if rec['qty_base'] is not None and abs(float(rec['qty_base'] or 0))>1e-9:
        return float(rec['qty_base']), 'oz'
    return 0.0, 'bottle'

def _movement_total_in_basis(ds,p,bar_id,types,direction,basis):
    col='qty_base' if basis in ('unit','oz') else 'qty_bottle_equiv'
    loc_col='to_location_id' if direction=='in' else 'from_location_id'
    marks=','.join('?' for _ in types)
    sql=f"SELECT COALESCE(SUM(COALESCE({col},0)),0) x FROM movements WHERE movement_date=? AND product_id=? AND {loc_col}=? AND movement_type IN ({marks})"
    r=one(sql,[ds,p['id'],bar_id,*types])
    return float(r['x'] or 0)

def transfers_in_basis(ds,p,bar_id,basis):
    return _movement_total_in_basis(ds,p,bar_id,('TRANSFER','SUPPLIER'),'in',basis)

def adjustments_basis(ds,p,bar_id,basis):
    return _movement_total_in_basis(ds,p,bar_id,('PRUEBA','DESPERDICIO','CORTESIA','ROTURA'),'out',basis)

def basis_qty_text(p,qty,basis,signed=False):
    if qty is None: return '—'
    v=float(qty); plus='+' if signed and v>0 else ''
    if basis=='unit': return f"{plus}{v:.0f} unid"
    if basis=='bottle': return f"{plus}{v:.2f} bot · oz pendiente"
    return dual_qty_text(p,v,signed=signed)

def physical_issue_text_basis(p,stock_gain,adjustment_excess,basis):
    if stock_gain and stock_gain>0:
        return f"⚠ Stock aumentó {basis_qty_text(p,stock_gain,basis)} sin entrada registrada"
    if adjustment_excess and adjustment_excess>0:
        return f"⚠ Ajustes superan la salida física por {basis_qty_text(p,adjustment_excess,basis)}"
    return '—'

def _session_trace_label(session):
    if not session: return '—'
    kind='Apertura' if session['session_type']=='OPENING' else 'Cierre'
    cyc='Semanal' if str(session['inventory_cycle'] or 'DAILY')=='WEEKLY' else 'Diario'
    return f"{kind} {cyc} · {session['employee'] or 'Usuario'} · {format_local_time(session['created_at'])} · ID {session['id']}"


# ---------------------- V0.6.0 cierre-only daily workflow ----------------------
# The live daily operation no longer uses OPENING sessions. Historical OPENING rows are
# preserved exactly as they were for audit/reports, but all new daily captures are CLOSING
# snapshots. A close may be saved partially (beer/liquor) and continued later. The next
# completed close is reconciled against the previous close plus entries/adjustments and POS.

CLOSE_ONLY_PREFIX='[CLOSE_ONLY_V1|'


def _is_historical_inventory_note_sql(alias='s'):
    # Historical paper transcriptions are audit records and never control the live close workflow.
    return f"COALESCE({alias}.notes,'') NOT LIKE '[TRANSCRIPCIÓN HISTÓRICA POR CONTINGENCIA%'"


def _build_close_only_marker(cycle_id, baseline_id, required_ids, operation_date):
    ids=','.join(str(int(x)) for x in sorted(set(required_ids or [])))
    return f"{CLOSE_ONLY_PREFIX}cycle={cycle_id}|baseid={int(baseline_id or 0)}|required={ids}|opdate={operation_date}]"


def _parse_close_only_marker(notes):
    txt=str(notes or '')
    pos=txt.find(CLOSE_ONLY_PREFIX)
    if pos<0:return None
    end=txt.find(']',pos)
    if end<0:return None
    body=txt[pos+len(CLOSE_ONLY_PREFIX):end]
    parts={}
    for token in body.split('|'):
        if '=' in token:
            k,v=token.split('=',1);parts[k.strip()]=v.strip()
    try:
        req={int(x) for x in parts.get('required','').split(',') if x.strip()}
        return {'cycle':parts.get('cycle') or '', 'baseid':int(parts.get('baseid') or 0),
                'required_ids':req,'opdate':parts.get('opdate') or ''}
    except Exception:
        return None


def _close_only_session_rows(cycle_id):
    if not cycle_id:return []
    needle=f"%{CLOSE_ONLY_PREFIX}cycle={cycle_id}|%"
    return q(f"""SELECT s.*,u.name employee,COUNT(ic.id) item_count
                 FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                 LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                 WHERE s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                   AND s.notes LIKE ? AND {_is_historical_inventory_note_sql('s')}
                 GROUP BY s.id ORDER BY s.id""",(needle,))


def _close_only_captured_ids(cycle_id):
    if not cycle_id:return set()
    needle=f"%{CLOSE_ONLY_PREFIX}cycle={cycle_id}|%"
    rows=q(f"""SELECT DISTINCT ic.product_id FROM inventory_counts ic
               JOIN inventory_sessions s ON s.id=ic.session_id
               WHERE s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                 AND s.notes LIKE ? AND {_is_historical_inventory_note_sql('s')}""",(needle,))
    return {int(r['product_id']) for r in rows}


def _latest_close_only_cycle():
    r=one(f"""SELECT s.id,s.session_date,s.notes,s.created_at,u.name employee
               FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
               WHERE s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                 AND s.notes LIKE ? AND {_is_historical_inventory_note_sql('s')}
               ORDER BY s.id DESC LIMIT 1""",(CLOSE_ONLY_PREFIX+'%',))
    if not r:return None
    m=_parse_close_only_marker(r['notes'])
    if not m or not m['cycle']:return None
    captured=_close_only_captured_ids(m['cycle'])
    complete=bool(m['required_ids']) and m['required_ids'].issubset(captured)
    return {'cycle_id':m['cycle'],'baseline_id':m['baseid'],'required_ids':m['required_ids'],
            'operation_date':m['opdate'] or r['session_date'],'captured_ids':captured,
            'required_count':len(m['required_ids']),'closing_count':len(m['required_ids'] & captured),
            'complete':complete,'latest_session_id':int(r['id']),'created_at':r['created_at'],'employee':r['employee']}


def _latest_daily_closing_boundary(operation_date=None):
    """Latest daily CLOSING available before a new close-only cycle starts.

    The operational date is preferred over insertion id so a historical paper transcription
    entered later cannot accidentally become the baseline for a newer day.
    """
    sql=f"""SELECT s.id,s.session_date,s.created_at,s.notes FROM inventory_sessions s
             WHERE s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
               AND {_is_historical_inventory_note_sql('s')}"""
    ps=[]
    if operation_date:
        ds=operation_date.isoformat() if hasattr(operation_date,'isoformat') else str(operation_date)
        sql += " AND s.session_date<=?";ps.append(ds)
    sql += " ORDER BY s.session_date DESC,s.id DESC LIMIT 1"
    r=one(sql,ps)
    return r


def _close_cycle_progress():
    latest=_latest_close_only_cycle()
    if latest and not latest['complete']:
        return {'active':True,**latest}
    return {'active':False,'cycle_id':None,'baseline_id':int(latest['latest_session_id']) if latest and latest['complete'] else 0,
            'required_ids':{int(p['id']) for p in inventory_products('DAILY')},'captured_ids':set(),
            'required_count':len(inventory_products('DAILY')),'closing_count':0,'complete':False,
            'operation_date':local_today().isoformat()}


def inventory_workflow_state():
    """Live workflow from V0.6.0: only CLOSING snapshots exist.

    There is no calendar/time gate and no OPENING prerequisite. If a partial close exists,
    users continue that same close until all required daily products are captured. Once
    complete, another close may start immediately on any operational date selected by the user.
    """
    p=_close_cycle_progress()
    try:d=date.fromisoformat(str(p['operation_date']))
    except Exception:d=local_today()
    return {'stage':'CLOSING','business_date':d,'cycle':'DAILY','progress':{
        'required_ids':p['required_ids'],'required_count':p['required_count'],
        'closing_ids':p['captured_ids'],'closing_count':p['closing_count'],
        'closing_complete':p['complete'],'opening_ids':set(),'opening_count':0,'opening_complete':False},
        'active':p['active'],'close_cycle_id':p.get('cycle_id'),'baseline_id':p.get('baseline_id',0)}


def _workflow_status_text(wf):
    p=wf['progress'];d=wf['business_date'].strftime('%d/%m/%Y')
    if wf.get('active'):
        return f"Cierre diario en progreso · fecha operativa {d} · {p['closing_count']}/{p['required_count']} productos"
    return f"Cierre diario disponible · puedes registrar el conteo cuando corresponda"


def _validate_inventory_save(kind,business_date,cycle):
    if kind=='OPENING':
        return False,'Las aperturas fueron deshabilitadas desde V0.6.0. El inventario diario se registra únicamente mediante cierres.'
    if kind!='CLOSING' or cycle!='DAILY':
        return False,'El inventario operativo diario solo admite cierres.'
    ds=business_date.isoformat() if hasattr(business_date,'isoformat') else str(business_date)
    try:
        if date.fromisoformat(ds)>local_today():
            return False,'La fecha operativa del cierre no puede estar en el futuro.'
    except Exception:
        return False,'Fecha operativa inválida.'
    p=_close_cycle_progress()
    if p.get('active') and ds!=str(p.get('operation_date')):
        return False,f"Ya existe un cierre parcial en progreso para {p.get('operation_date')}. Debes terminarlo antes de iniciar otro cierre."
    return True,''


def _baseline_count_before_id(pid,lid,baseline_id):
    if not baseline_id:return None
    return one(f"""SELECT ic.qty_base,ic.qty_bottle_equiv,s.id session_id,s.session_date,s.created_at,
                           u.name employee,COALESCE(s.notes,'') notes
                    FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                    LEFT JOIN users u ON u.id=s.user_id
                    WHERE s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                      AND ic.product_id=? AND ic.location_id=? AND s.id<=?
                      AND {_is_historical_inventory_note_sql('s')}
                    ORDER BY s.session_date DESC,s.id DESC,ic.id DESC LIMIT 1""",(int(pid),int(lid),int(baseline_id)))


def _latest_close_only_cycle_for_date(ds):
    r=one(f"""SELECT s.notes,s.id FROM inventory_sessions s
               WHERE s.session_date=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                 AND s.notes LIKE ? AND {_is_historical_inventory_note_sql('s')}
               ORDER BY s.id DESC LIMIT 1""",(str(ds),CLOSE_ONLY_PREFIX+'%'))
    if not r:return None
    m=_parse_close_only_marker(r['notes'])
    return m if m and m.get('cycle') else None


def _latest_closing_count_on_date(ds,pid,lid):
    cycle=_latest_close_only_cycle_for_date(ds)
    if cycle:
        needle=f"%{CLOSE_ONLY_PREFIX}cycle={cycle['cycle']}|%"
        return one(f"""SELECT ic.qty_base,ic.qty_bottle_equiv,s.id session_id,s.session_date,s.created_at,
                               u.name employee,COALESCE(s.notes,'') notes
                        FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                        LEFT JOIN users u ON u.id=s.user_id
                        WHERE s.session_date=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                          AND s.notes LIKE ? AND ic.product_id=? AND ic.location_id=?
                        ORDER BY s.id DESC,ic.id DESC LIMIT 1""",(str(ds),needle,int(pid),int(lid)))
    return one(f"""SELECT ic.qty_base,ic.qty_bottle_equiv,s.id session_id,s.session_date,s.created_at,
                           u.name employee,COALESCE(s.notes,'') notes
                    FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                    LEFT JOIN users u ON u.id=s.user_id
                    WHERE s.session_date=? AND s.session_type='CLOSING'
                      AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                      AND ic.product_id=? AND ic.location_id=?
                    ORDER BY s.id DESC,ic.id DESC LIMIT 1""",(str(ds),int(pid),int(lid)))


def _previous_closing_count_for_record(current_rec,pid,lid):
    if current_rec is None:return None
    marker=_parse_close_only_marker(current_rec['notes'])
    if marker:
        return _baseline_count_before_id(pid,lid,marker['baseid'])
    # Legacy fallback: use the latest closing from a strictly earlier operational date.
    return one(f"""SELECT ic.qty_base,ic.qty_bottle_equiv,s.id session_id,s.session_date,s.created_at,
                           u.name employee,COALESCE(s.notes,'') notes
                    FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                    LEFT JOIN users u ON u.id=s.user_id
                    WHERE s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                      AND ic.product_id=? AND ic.location_id=? AND s.session_date<?
                      AND {_is_historical_inventory_note_sql('s')}
                    ORDER BY s.session_date DESC,s.id DESC,ic.id DESC LIMIT 1""",
               (int(pid),int(lid),str(current_rec['session_date'])))


def _window_dates(previous_date,current_date):
    if not current_date:return []
    try:cur=date.fromisoformat(str(current_date))
    except Exception:return []
    if not previous_date:return [cur.isoformat()]
    try:prev=date.fromisoformat(str(previous_date))
    except Exception:return [cur.isoformat()]
    if cur<=prev:return [cur.isoformat()]
    return [d.isoformat() for d in date_range(prev+timedelta(days=1),cur)]


def _movement_total_window_in_basis(previous_rec,current_rec,p,bar_id,types,direction,basis):
    dates=_window_dates(previous_rec['session_date'] if previous_rec else None,current_rec['session_date'] if current_rec else None)
    if not dates:return 0.0
    col='qty_base' if basis in ('unit','oz') else 'qty_bottle_equiv'
    loc_col='to_location_id' if direction=='in' else 'from_location_id'
    marks=','.join('?' for _ in types);dmarks=','.join('?' for _ in dates)
    sql=f"SELECT COALESCE(SUM(COALESCE({col},0)),0) x FROM movements WHERE product_id=? AND {loc_col}=? AND movement_date IN ({dmarks}) AND movement_type IN ({marks})"
    r=one(sql,[p['id'],bar_id,*dates,*types]);return float(r['x'] or 0)


def _pos_window_ready(previous_rec,current_rec,p):
    dates=_window_dates(previous_rec['session_date'] if previous_rec else None,current_rec['session_date'] if current_rec else None)
    return bool(dates) and all(pos_comparison_ready(ds,p) for ds in dates)


def _expected_sales_window(previous_rec,current_rec,p):
    dates=_window_dates(previous_rec['session_date'] if previous_rec else None,current_rec['session_date'] if current_rec else None)
    return sum(expected_sales(ds,p['id'],p) for ds in dates)


def _close_cycle_marker_for_save(operation_date):
    p=_close_cycle_progress()
    ds=operation_date.isoformat() if hasattr(operation_date,'isoformat') else str(operation_date)
    if p.get('active'):
        if str(p.get('operation_date'))!=ds:
            raise RuntimeError(f"Existe un cierre parcial para {p.get('operation_date')}; complétalo antes de iniciar otro.")
        # Read the exact marker from the latest session so all partial captures share lineage.
        r=one("SELECT notes FROM inventory_sessions WHERE id=?",(int(p['latest_session_id']),))
        marker_txt=str(r['notes'] or '') if r else ''
        parsed=_parse_close_only_marker(marker_txt)
        marker=marker_txt[marker_txt.find(CLOSE_ONLY_PREFIX):marker_txt.find(']',marker_txt.find(CLOSE_ONLY_PREFIX))+1] if parsed else None
        if marker:return marker,parsed
    required={int(x['id']) for x in inventory_products('DAILY')}
    baseline=_latest_daily_closing_boundary(operation_date)
    baseid=int(baseline['id']) if baseline else 0
    cycle_id=uuid.uuid4().hex[:12]
    marker=_build_close_only_marker(cycle_id,baseid,required,ds)
    return marker,{'cycle':cycle_id,'baseid':baseid,'required_ids':required,'opdate':ds}


def daily_close_progress():
    p=_close_cycle_progress()
    return p


def day_product_reconciliation(ds,p,bar_id):
    """Reconcile a physical CLOSING against the immediately previous CLOSING.

    New V0.6.0 rows use an immutable baseline boundary embedded in their close-cycle marker.
    Legacy rows fall back to the latest close from an earlier operational date. OPENING rows
    remain stored for history but are never required for this calculation.
    """
    current=_latest_closing_count_on_date(ds,p['id'],bar_id)
    if current is None:return None
    previous=_previous_closing_count_for_record(current,p['id'],bar_id)
    cv,cbasis=_count_value_for_reconciliation(p,current)
    if previous is None:
        return {'opening':None,'closing':cv,'basis':cbasis,'entries':0.0,'adjustments':0.0,
                'physical':0.0,'count_sale':0.0,'stock_gain':0.0,'adjustment_excess':0.0,
                'pos_ready':False,'pos_sale':None,'diff':None,'baseline_missing':True,
                'opening_session_id':None,'opening_created_at':None,'opening_employee':None,
                'closing_session_id':current['session_id'],'closing_created_at':current['created_at'],
                'closing_employee':current['employee'],'cycle':'DAILY','previous_close':None,'current_close':cv}
    pv,pbasis=_count_value_for_reconciliation(p,previous)
    if pv is None or cv is None or pbasis!=cbasis:return None
    basis=pbasis
    entries=_movement_total_window_in_basis(previous,current,p,bar_id,('TRANSFER','SUPPLIER'),'in',basis)
    adj=_movement_total_window_in_basis(previous,current,p,bar_id,('PRUEBA','DESPERDICIO','CORTESIA','ROTURA'),'out',basis)
    rec=reconciliation_values(pv,cv,entries,adj)
    ready=(basis!='bottle' and _pos_window_ready(previous,current,p))
    pos=_expected_sales_window(previous,current,p) if ready else None
    diff=(rec['count_sale']-pos) if ready else None
    return {'opening':pv,'closing':cv,'basis':basis,'entries':entries,'adjustments':adj,
            'physical':rec['physical'],'count_sale':rec['count_sale'],'stock_gain':rec['stock_gain'],
            'adjustment_excess':rec['adjustment_excess'],'pos_ready':ready,'pos_sale':pos,'diff':diff,
            'baseline_missing':False,
            'opening_session_id':previous['session_id'],'opening_created_at':previous['created_at'],'opening_employee':previous['employee'],
            'closing_session_id':current['session_id'],'closing_created_at':current['created_at'],'closing_employee':current['employee'],'cycle':'DAILY',
            'previous_close':pv,'current_close':cv,'previous_close_date':previous['session_date']}

def transfers_in(d,pid,bar_id):
    r=one("SELECT COALESCE(SUM(qty_base),0) x FROM movements WHERE movement_date=? AND product_id=? AND to_location_id=? AND movement_type IN ('TRANSFER','SUPPLIER')",(d,pid,bar_id))
    return float(r['x'] or 0)

def adjustments(d,pid,bar_id):
    r=one("SELECT COALESCE(SUM(qty_base),0) x FROM movements WHERE movement_date=? AND product_id=? AND from_location_id=? AND movement_type IN ('PRUEBA','DESPERDICIO','CORTESIA','ROTURA')",(d,pid,bar_id))
    return float(r['x'] or 0)

def expected_sales(d,pid,p):
    """Venta explicada por POS. Cerveza=unidades; licor=oz."""
    total=0.0
    rows=q("SELECT sale_type,quantity,oz_per_unit FROM pos_sales WHERE sale_date=? AND product_id=?",(d,pid))
    for r in rows:
        if p['category']=='Cerveza':
            total += float(r['quantity'])
        elif r['oz_per_unit'] is not None:
            total += float(r['quantity'])*float(r['oz_per_unit'])
        elif r['sale_type']=='Botella de licor' and p['bottle_ml']:
            total += float(r['quantity'])*(float(p['bottle_ml'])/ML_PER_OZ)
    rr=q("""SELECT ps.quantity,r.oz_qty FROM pos_sales ps JOIN recipes r ON r.cocktail_id=ps.cocktail_id
            WHERE ps.sale_date=? AND ps.sale_type='Cóctel' AND r.product_id=?""",(d,pid))
    total += sum(float(x['quantity'])*float(x['oz_qty']) for x in rr)
    return total


@_serialized_durable_write
def record_pos_batch(d,sale_group,note=""):
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:raise RuntimeError(guard_msg)
    if SYNC_PREFLIGHT_STATUS.get('status')=='conflict':
        raise RuntimeError('Sincronización en conflicto. POS bloqueado para evitar pérdida de datos.')
    ds=d.isoformat() if hasattr(d,'isoformat') else str(d)
    con.execute("INSERT INTO pos_batches(sale_date,sale_group,user_id,note,created_at) VALUES(?,?,?,?,?)",
                (ds,sale_group,user['id'],note,now_iso()))
    con.commit()
    ok,msg=_confirmed_backup_after_write()
    if not ok:raise RuntimeError('POS guardado localmente, pero el respaldo durable quedó pendiente: '+msg)


@_serialized_durable_write
def save_pos_group(d,sale_group,rows,note=""):
    """Save POS detail rows and the confirmation batch in one SQLite transaction and one durable backup."""
    guard_ok,guard_msg=_write_sync_guard()
    if not guard_ok:return {'ok':False,'error':guard_msg}
    ds=d.isoformat() if hasattr(d,'isoformat') else str(d);created=now_iso()
    try:
        con.execute('BEGIN IMMEDIATE')
        for r in rows:
            con.execute("INSERT INTO pos_sales(sale_date,cocktail_id,product_id,sale_type,quantity,oz_per_unit,user_id,observation,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (ds,r.get('cocktail_id'),r.get('product_id'),r['sale_type'],r['quantity'],r.get('oz_per_unit'),user['id'],note,created))
        con.execute("INSERT INTO pos_batches(sale_date,sale_group,user_id,note,created_at) VALUES(?,?,?,?,?)",
                    (ds,sale_group,user['id'],note,created))
        con.commit()
    except Exception as exc:
        con.rollback();return {'ok':False,'error':str(exc)}
    bok,bmsg=_confirmed_backup_after_write()
    return {'ok':True,'backup_ok':bok,'backup_message':bmsg,'created_at':created}


def pos_group_submitted(ds,sale_group):
    if one("SELECT 1 FROM pos_batches WHERE sale_date=? AND sale_group=? LIMIT 1",(ds,sale_group)):
        return True
    mapping={'BEER':'Cerveza','COCKTAIL':'Cóctel','SHOT':'Shot','LIQUOR_BOTTLE':'Botella de licor'}
    stype=mapping.get(sale_group)
    return bool(stype and one("SELECT 1 FROM pos_sales WHERE sale_date=? AND sale_type=? LIMIT 1",(ds,stype)))


def pos_comparison_ready(ds,p):
    if p['category']=='Cerveza':
        return pos_group_submitted(ds,'BEER')
    if p['category']=='Licor':
        return all(pos_group_submitted(ds,g) for g in ('COCKTAIL','SHOT','LIQUOR_BOTTLE'))
    return False


def dual_qty_text(p,qty,signed=False,beer_label='unid'):
    """Licor siempre en oz + botellas equivalentes; cerveza en unidades."""
    if qty is None: return '—'
    v=float(qty); plus='+' if signed and v>0 else ''
    if p['category']=='Cerveza': return f"{plus}{v:.0f} {beer_label}"
    boz=bottle_oz(p)
    if not boz: return f"{plus}{v:.2f} oz · ⚠ Falta ml"
    b=v/boz; bplus='+' if signed and b>0 else ''
    return f"{plus}{v:.2f} oz · {bplus}{b:.2f} bot"



def reconciliation_values(previous_close, current_close, entries=0.0, adj=0.0):
    """
    Reconciliación física cierre-contra-cierre con cantidades no negativas.

    Salida física = max(cierre anterior + entradas - cierre actual, 0).
    Venta por conteo = max(salida física - ajustes autorizados, 0).

    Si el cierre actual supera cierre anterior + entradas, no se presenta consumo negativo:
    se registra como aumento de stock no explicado para revisión.
    """
    previous_close=float(previous_close or 0); current_close=float(current_close or 0)
    entries=max(float(entries or 0),0.0); adj=max(float(adj or 0),0.0)
    raw_out=previous_close + entries - current_close
    physical=max(raw_out,0.0)
    stock_gain=max(-raw_out,0.0)
    count_sale=max(physical-adj,0.0)
    adjustment_excess=max(adj-physical,0.0)
    return {
        'raw_out':raw_out, 'physical':physical, 'stock_gain':stock_gain,
        'adjustments':adj, 'count_sale':count_sale, 'adjustment_excess':adjustment_excess
    }

def physical_issue_text(p, stock_gain=0.0, adjustment_excess=0.0):
    if stock_gain and stock_gain>0:
        return f"⚠ Stock aumentó {dual_qty_text(p,stock_gain)} sin entrada registrada"
    if adjustment_excess and adjustment_excess>0:
        return f"⚠ Ajustes superan la salida física por {dual_qty_text(p,adjustment_excess)}"
    return '—'

def opening_variance(d,pid,bar_id):
    r=one("""SELECT ic.variance FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             WHERE s.session_date=? AND s.session_type='OPENING' AND ic.product_id=? AND ic.location_id=?
             ORDER BY s.created_at DESC LIMIT 1""",(d,pid,bar_id))
    return float(r['variance']) if r and r['variance'] is not None else None

def date_range(d1,d2):
    cur=d1
    while cur<=d2:
        yield cur
        cur += timedelta(days=1)

def consolidated(d1,d2):
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    rows=[]
    for p in products():
        if p['category'] not in ('Cerveza','Licor'): continue
        physical=pos_total=adj=trans=count_sales=stock_gain=adjustment_excess=0.0; days_complete=days_pos=0
        first_open=last_close_val=None; basis=('unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle'))
        for dd in date_range(d1,d2):
            ds=dd.isoformat(); dr=day_product_reconciliation(ds,p,bar)
            if not dr: continue
            basis=dr['basis']
            if first_open is None: first_open=dr['opening']
            last_close_val=dr['closing']
            physical+=dr['physical']; adj+=dr['adjustments']; trans+=dr['entries']; count_sales+=dr['count_sale']; stock_gain+=dr['stock_gain']; adjustment_excess+=dr['adjustment_excess']; days_complete+=1
            if dr['pos_ready']:
                pos_total+=float(dr['pos_sale'] or 0); days_pos+=1
        pos_ready=days_complete>0 and days_pos==days_complete; diff=(count_sales-pos_total) if pos_ready else None
        state_code,state_label,diff_text=_difference_state(p,diff,days_complete>0,pos_ready=pos_ready)
        if basis=='bottle' and days_complete>0 and stock_gain<=0 and adjustment_excess<=0:
            state_code,state_label,diff_text=('PENDING','⚠ Falta ml para POS','—')
        if stock_gain>0:
            state_code,state_label=('ALERT','🔴 Revisar entradas/conteo')
        elif adjustment_excess>0:
            state_code,state_label=('REVIEW','🟡 Revisar ajustes')
        rows.append({'Producto':product_label(p),'Categoría':p['category'],'Inicial':first_open,'Final':last_close_val,
            'Entradas al bar':trans,'Consumo real':physical,'Consumo físico':physical,'Ajustes':adj,
            'Venta por conteo':count_sales,'Ventas POS':pos_total,'Consumo esperado':pos_total,
            'Diferencia no explicada':diff,'Diferencia':diff,'Estado':state_label,'Días completos':days_complete,
            'Días POS completos':days_pos,'_state':state_code,'_diff_text':diff_text,
            '_pid':p['id'],'_unit':unit_label(p),'_p':p,'_basis':basis,
            'Incidencia física':physical_issue_text_basis(p,stock_gain,adjustment_excess,basis),
            '_stock_gain':stock_gain,'_adjustment_excess':adjustment_excess})
    return rows

def current_stock_basis(p, location_id):
    """Current physical stock using the newest valid physical count.

    Daily Opening/Closing counts and COMPLETED independent weekly snapshots compete only by
    actual capture timestamp.  An in-progress weekly inventory never becomes stock truth, which
    prevents a half-counted weekly session from distorting replenishment. Movements after the
    selected count are then applied in the same unit basis.
    """
    daily=one("""SELECT ic.qty_base,ic.qty_bottle_equiv,s.session_date base_date,s.created_at base_created,'DAILY' source
                 FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                 WHERE ic.product_id=? AND ic.location_id=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                 ORDER BY s.created_at DESC,s.id DESC,ic.id DESC LIMIT 1""",(p['id'],location_id))
    weekly=one("""SELECT wc.qty_base,wc.qty_bottle_equiv,w.inventory_date base_date,wc.created_at base_created,'WEEKLY' source
                  FROM weekly_inventory_counts wc JOIN weekly_inventory_sessions w ON w.id=wc.weekly_session_id
                  WHERE wc.product_id=? AND wc.location_id=? AND w.status='COMPLETED'
                  ORDER BY wc.created_at DESC,wc.id DESC LIMIT 1""",(p['id'],location_id))
    candidates=[r for r in (daily,weekly) if r is not None]
    r=max(candidates,key=lambda x:str(x['base_created'] or '')) if candidates else None
    basis='unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle')
    if r:
        if basis in ('unit','oz'): base=float(r['qty_base'] or 0)
        elif r['qty_bottle_equiv'] is not None: base=float(r['qty_bottle_equiv'])
        elif abs(float(r['qty_base'] or 0))>1e-9:
            basis='oz'; base=float(r['qty_base'])
        else: base=0.0
        base_created=r['base_created']
        if str(r['source'])=='WEEKLY':
            # Weekly sessions may be completed across midnight. Movements must be applied
            # relative to the actual local capture date of this product, not only the session start date.
            captured_local=to_local_datetime(base_created)
            base_date=captured_local.date().isoformat() if captured_local else r['base_date']
        else:
            base_date=r['base_date']
        time_clause=" AND (movement_date>? OR (movement_date=? AND created_at>?))"
        time_params=(base_date,base_date,base_created)
    else:
        base=0.0; time_clause=''; time_params=()
    col='qty_bottle_equiv' if basis=='bottle' else 'qty_base'
    incoming=one(f"SELECT COALESCE(SUM(COALESCE({col},0)),0) x FROM movements WHERE product_id=? AND to_location_id=?{time_clause}",(p['id'],location_id,*time_params))['x']
    outgoing=one(f"SELECT COALESCE(SUM(COALESCE({col},0)),0) x FROM movements WHERE product_id=? AND from_location_id=?{time_clause}",(p['id'],location_id,*time_params))['x']
    return max(base + float(incoming or 0)-float(outgoing or 0),0.0),basis

def current_stock(pid, location_id):
    # Compatibility wrapper for legacy callers. Prefer current_stock_basis when unit context matters.
    p=one("SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.id=?",(pid,))
    if not p: return 0.0
    val,basis=current_stock_basis(p,location_id)
    return val

def bottle_oz(p):
    return (float(p['bottle_ml'])/ML_PER_OZ) if p['category']=='Licor' and p['bottle_ml'] else None

def oz_and_bottles_text(p, qty, beer_label='unid'):
    qty=max(float(qty or 0),0)
    if p['category']=='Cerveza':
        return f"{qty:.0f} {beer_label}"
    boz=bottle_oz(p)
    if not boz:
        return f"{qty:.2f} oz\n⚠ Falta ml"
    return f"{qty:.2f} oz\n{qty/boz:.2f} bot"

def difference_cost(r):
    p=r['_p']; cost=p['unit_cost']
    if cost is None: return None
    diff=abs(float(r['Diferencia no explicada'] or 0))
    if p['category']=='Cerveza': return diff*float(cost)
    boz=bottle_oz(p)
    return (diff/boz*float(cost)) if boz else None

def product_accuracy(r):
    base=abs(float(r.get('Venta por conteo',r.get('Consumo real',0)) or 0))
    diffv=r.get('Diferencia no explicada',r.get('Diferencia'))
    if diffv is None or base<=0: return None
    return max(0.0,min(100.0,(1.0-abs(float(diffv))/base)*100.0))

def daily_trend(d1,d2,category):
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; out=[]
    for dd in date_range(d1,d2):
        count_sale=pos_sale=0.0; complete=False; pos_ready=True; comparable_count=0; ds=dd.isoformat()
        for p in products(category):
            dr=day_product_reconciliation(ds,p,bar)
            if not dr: continue
            # Liquor without ml is kept in bottles and cannot be mixed into an oz chart.
            if category=='Licor' and dr['basis']!='oz':
                continue
            count_sale += dr['count_sale']; complete=True; comparable_count+=1
            if dr['pos_ready']: pos_sale += float(dr['pos_sale'] or 0)
            else: pos_ready=False
        if complete and comparable_count:
            out.append({'Fecha':ds,'Venta por conteo':count_sale,'Ventas POS':(pos_sale if pos_ready else None)})
    return pd.DataFrame(out)

# --------------------------- Dashboard operacional V0.4.8 ---------------------------
def _latest_count_record(ds, pid, kind, bar_id):
    # Backward-compatible helper. Dashboard/reports use coherent session pairs in V0.4.8.
    sess=_inventory_session(ds,kind)
    if not sess: return None
    rec=_count_record_for_session(sess['id'],pid,bar_id)
    if not rec: return None
    out=dict(rec); out.update({'created_at':sess['created_at'],'inventory_cycle':sess['inventory_cycle'],'employee':sess['employee'],'session_id':sess['id']})
    return out

def _latest_cycle_for_date(ds):
    op,cl,cycle=_paired_inventory_sessions(ds)
    return cycle

def _count_text(p, base, bottle_equiv=None):
    if base is None and bottle_equiv is None:
        return '—'
    if p['category']=='Cerveza':
        return f"{float(base or 0):.0f} botellas"
    beq=bottle_equiv
    boz=bottle_oz(p)
    if beq is None and boz and base is not None:
        beq=float(base)/boz
    if beq is not None and base is not None and p['bottle_ml']:
        return f"{float(beq):.2f} bot · {float(base):.2f} oz"
    if beq is not None:
        return f"{float(beq):.2f} bot · oz pendiente"
    if base is not None and abs(float(base or 0))>1e-9:
        return f"{float(base):.2f} oz · presentación pendiente"
    return "0.00 bot · oz pendiente"

def _base_expected_text(p, base):
    if base is None:
        return '—'
    if p['category']=='Cerveza':
        return f"{float(base):.0f} botellas"
    boz=bottle_oz(p)
    if boz:
        return f"{float(base)/boz:.2f} bot · {float(base):.2f} oz"
    return f"{float(base):.2f} oz"

def _difference_state(p, diff, registered=True, pos_ready=True):
    if not registered: return ('PENDING','⏳ Pendiente','—')
    if not pos_ready: return ('PENDING','🔵 Pendiente POS','—')
    if diff is None: return ('PENDING','⏳ Pendiente','—')
    tol=float(setting('tolerance_beer','1')) if p['category']=='Cerveza' else float(setting('tolerance_liquor','1'))
    ad=abs(float(diff)); diff_text=dual_qty_text(p,diff,signed=True)
    if ad<=tol: return ('OK','🟢 OK',diff_text)
    if ad<=tol*3: return ('REVIEW','🟡 Revisar',diff_text)
    return ('ALERT','🔴 Alerta',diff_text)

def _snapshot_products_for_date_cycle(ds,cycle):
    """Historical view = products actually counted; current day = configured requirements + actual counts."""
    historical=ds < local_today().isoformat()
    base={} if historical else {p['id']:p for p in inventory_products(cycle)}
    rows=q("""SELECT DISTINCT p.*,c.name category,c.count_unit
              FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
              JOIN products p ON p.id=ic.product_id JOIN categories c ON c.id=p.category_id
              WHERE s.session_date=? AND COALESCE(s.inventory_cycle,'DAILY')=? AND c.name IN ('Cerveza','Licor')""",(ds,cycle))
    for p in rows: base[p['id']]=p
    return sorted(base.values(),key=lambda p:(p['category'],p['name']))

def today_inventory_snapshot(target_date=None, preferred_cycle=None):
    """Dashboard snapshot for the close-only daily model.

    The physical baseline is the previous CLOSING, never an OPENING. Historical OPENING
    sessions remain visible only in audit views and are not required for operational KPIs.
    """
    target_date=target_date or local_today();ds=target_date.isoformat()
    bar_id=one("SELECT id FROM locations WHERE name='Bar'")['id']
    cycle='DAILY';rows=[]
    product_map={p['id']:p for p in inventory_products('DAILY')}
    historical=q("""SELECT DISTINCT p.*,c.name category,c.count_unit
                    FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                    JOIN products p ON p.id=ic.product_id JOIN categories c ON c.id=p.category_id
                    WHERE s.session_date=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                      AND c.name IN ('Cerveza','Licor')""",(ds,))
    for p in historical:product_map[p['id']]=p
    for p in sorted(product_map.values(),key=lambda x:(x['category'],x['name'])):
        cur=_latest_closing_count_on_date(ds,p['id'],bar_id)
        prev=_previous_closing_count_for_record(cur,p['id'],bar_id) if cur else one(f"""SELECT ic.qty_base,ic.qty_bottle_equiv,s.id session_id,s.session_date,s.created_at,
                           u.name employee,COALESCE(s.notes,'') notes
                    FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                    LEFT JOIN users u ON u.id=s.user_id
                    WHERE s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                      AND ic.product_id=? AND ic.location_id=? AND s.session_date<?
                      AND {_is_historical_inventory_note_sql('s')}
                    ORDER BY s.session_date DESC,s.id DESC,ic.id DESC LIMIT 1""",(p['id'],bar_id,ds))
        registered=cur is not None;physical=adj=count_sale=pos_sale=diff=None;stock_gain=adjustment_excess=0.0;ready=False
        basis='unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle')
        dr=day_product_reconciliation(ds,p,bar_id) if cur else None
        if cur is None:
            state_code,state_label,diff_text=('PENDING','⏳ Pendiente cierre','—');basis_text='Último cierre disponible como referencia'
        elif dr is None:
            state_code,state_label,diff_text=('PENDING','⚠ Base de medida incompatible','—');basis_text='Revisar presentación histórica'
        elif dr.get('baseline_missing'):
            state_code,state_label,diff_text=('PENDING','🔵 Cierre base','—');basis_text='Primer cierre disponible para este producto; será la base del próximo periodo'
            basis=dr['basis']
        else:
            basis=dr['basis'];physical=dr['physical'];adj=dr['adjustments'];count_sale=dr['count_sale'];stock_gain=dr['stock_gain'];adjustment_excess=dr['adjustment_excess'];ready=dr['pos_ready'];pos_sale=dr['pos_sale'];diff=dr['diff']
            if basis=='bottle':
                state_code,state_label,diff_text=('PENDING','⚠ Falta ml para POS','—');basis_text='Cierres comparables en botellas · falta ml para POS/recetas'
            else:
                basis_text='Cierre anterior vs cierre actual + movimientos, comparado con POS' if ready else 'Cierres comparables · POS pendiente'
                state_code,state_label,diff_text=_difference_state(p,diff,True,pos_ready=ready)
            if stock_gain>0:state_code,state_label=('ALERT','🔴 Revisar entradas/conteo')
            elif adjustment_excess>0:state_code,state_label=('REVIEW','🟡 Revisar ajustes')
        prev_base=float(prev['qty_base']) if prev else None;prev_beq=float(prev['qty_bottle_equiv']) if prev and prev['qty_bottle_equiv'] is not None else None
        cur_base=float(cur['qty_base']) if cur else None;cur_beq=float(cur['qty_bottle_equiv']) if cur and cur['qty_bottle_equiv'] is not None else None
        entries=dr['entries'] if dr and not dr.get('baseline_missing') else None
        rows.append({'Producto':p['name'],'Tipo':p['category'],
            'Cierre anterior':_count_text(p,prev_base,prev_beq),'Cierre actual':_count_text(p,cur_base,cur_beq),
            # Backward-compatible aliases used by some report helpers.
            'Apertura':_count_text(p,prev_base,prev_beq),'Cierre':_count_text(p,cur_base,cur_beq),
            'Entradas':basis_qty_text(p,entries,basis) if entries is not None else '—',
            'Consumo físico':basis_qty_text(p,physical,basis),'Ajustes':basis_qty_text(p,adj,basis),
            'Venta por conteo':basis_qty_text(p,count_sale,basis),
            'Incidencia física':physical_issue_text_basis(p,stock_gain,adjustment_excess,basis),
            'Ventas POS / recetas':(basis_qty_text(p,pos_sale,basis) if ready else ('⚠ Falta ml para comparar' if basis=='bottle' and cur is not None else ('Pendiente POS' if cur is not None and prev is not None else '—'))),
            'Diferencia':diff_text,'Alerta':state_label,'Estado':'Registrado' if registered else 'Pendiente','Base comparación':basis_text,
            'Empleado':(cur['employee'] if cur else '—'),'Hora':(format_local_time(cur['created_at']) if cur else '—'),
            '_state':state_code,'_diff':diff,'_p':p,'_pid':p['id'],'_registered':registered,
            '_has_opening':prev is not None,'_has_closing':cur is not None,'_pos_ready':ready,'_physical':physical,
            '_adjustments':adj,'_count_sale':count_sale,'_pos_sale':pos_sale,'_stock_gain':stock_gain,
            '_adjustment_excess':adjustment_excess,'_basis':basis,
            '_opening_session_id':prev['session_id'] if prev else None,'_closing_session_id':cur['session_id'] if cur else None})
    return rows,cycle

def _inventory_progress_today(snapshot):
    total=len(snapshot);registered=sum(1 for r in snapshot if r['_registered'])
    baseline_exists=any(r['_has_opening'] for r in snapshot);close_done=total>0 and registered==total
    if total==0:state='Sin productos configurados'
    elif close_done:state='Cierre completo'
    elif registered>0:state='Cierre en progreso'
    else:state='Pendiente cierre'
    return total,registered,baseline_exists,close_done,state

def _category_progress(snapshot, category):
    rows=[r for r in snapshot if r['Tipo']==category]
    total=len(rows); done=sum(1 for r in rows if r['_registered'])
    if total==0: return 'No configurados'
    if done==0: return f'Pendientes · 0/{total}'
    if done<total: return f'En progreso · {done}/{total}'
    return f'Registradas · {done}/{total}'

def _last_inventory_activity(ds):
    return one("""SELECT s.created_at,u.name employee,s.session_type,s.inventory_cycle,COUNT(ic.id) item_count
                  FROM inventory_sessions s
                  LEFT JOIN users u ON u.id=s.user_id
                  LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                  WHERE s.session_date=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                  GROUP BY s.id
                  ORDER BY s.created_at DESC LIMIT 1""",(ds,))

def _latest_inventory_date_in_period(d1,d2):
    """Última fecha con inventario dentro del periodo seleccionado."""
    r=one("SELECT MAX(session_date) ds FROM inventory_sessions WHERE session_type='CLOSING' AND session_date BETWEEN ? AND ? AND COALESCE(inventory_cycle,'DAILY')='DAILY'",
          (d1.isoformat(),d2.isoformat()))
    if not r or not r['ds']:
        return None
    try:
        return datetime.strptime(str(r['ds']),'%Y-%m-%d').date()
    except Exception:
        return None

def recent_activity(limit=8):
    items=[]
    # Inventarios
    for r in q("""SELECT s.created_at,u.name employee,s.session_type,s.inventory_cycle,COUNT(ic.id) qty
                  FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                  LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                  GROUP BY s.id ORDER BY s.created_at DESC LIMIT 20"""):
        kind='Apertura' if r['session_type']=='OPENING' else 'Cierre'
        cycle='semanal' if str(r['inventory_cycle'])=='WEEKLY' else 'diario'
        items.append((r['created_at'],r['employee'] or 'Usuario',f"{kind} {cycle} · {int(r['qty'] or 0)} productos"))
    # Inventario semanal independiente
    for r in q("""SELECT wc.created_at,u.name employee,w.inventory_date,COUNT(wic.id) qty
                  FROM weekly_inventory_captures wc
                  JOIN weekly_inventory_sessions w ON w.id=wc.weekly_session_id
                  LEFT JOIN users u ON u.id=wc.user_id
                  LEFT JOIN weekly_inventory_counts wic ON wic.capture_id=wc.id
                  GROUP BY wc.id ORDER BY wc.created_at DESC LIMIT 20"""):
        items.append((r['created_at'],r['employee'] or 'Usuario',f"Inventario semanal · avance {int(r['qty'] or 0)} productos · fecha {r['inventory_date']}"))
    for r in q("""SELECT w.completed_at,u.name employee,w.inventory_date
                  FROM weekly_inventory_sessions w LEFT JOIN users u ON u.id=w.completed_by_user_id
                  WHERE w.status='COMPLETED' AND w.completed_at IS NOT NULL
                  ORDER BY w.completed_at DESC LIMIT 10"""):
        items.append((r['completed_at'],r['employee'] or 'Usuario',f"Inventario semanal finalizado · {r['inventory_date']}"))
    # POS agrupado por guardado/tipo
    for r in q("""SELECT ps.created_at,u.name employee,ps.sale_type,SUM(ps.quantity) qty
                  FROM pos_sales ps LEFT JOIN users u ON u.id=ps.user_id
                  GROUP BY ps.created_at,ps.user_id,ps.sale_type ORDER BY ps.created_at DESC LIMIT 20"""):
        items.append((r['created_at'],r['employee'] or 'Usuario',f"POS {r['sale_type']} · {float(r['qty'] or 0):g}"))
    # Movimientos
    labels={'SUPPLIER':'Recepción proveedor','TRANSFER':'Traslado Bodega → Bar','PRUEBA':'Prueba','DESPERDICIO':'Desperdicio','CORTESIA':'Cortesía','ROTURA':'Rotura / botella quebrada'}
    for r in q("""SELECT m.created_at,u.name employee,m.movement_type,p.name product,m.qty_base,m.qty_bottle_equiv
                  FROM movements m LEFT JOIN users u ON u.id=m.user_id JOIN products p ON p.id=m.product_id
                  ORDER BY m.created_at DESC LIMIT 20"""):
        items.append((r['created_at'],r['employee'] or 'Usuario',f"{labels.get(r['movement_type'],r['movement_type'])} · {r['product']}"))
    items=[x for x in items if x[0]]
    items.sort(key=lambda x:x[0],reverse=True)
    out=[]
    for created,employee,action in items[:limit]:
        try: when=format_local_datetime(created)
        except Exception: when=str(created)
        out.append({'Fecha / hora':when,'Usuario':employee,'Acción':action})
    return out

def period_inventory_performance(d1,d2):
    """Period reconciliation using coherent session pairs and the best physical basis available."""
    bar_id=one("SELECT id FROM locations WHERE name='Bar'")['id']; rows=[]
    for p in products():
        if p['category'] not in ('Cerveza','Licor'): continue
        physical=adj=count_sale=pos_sale=stock_gain=adjustment_excess=0.0; complete=pos_complete=0
        basis=('unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle'))
        for dd in date_range(d1,d2):
            dr=day_product_reconciliation(dd.isoformat(),p,bar_id)
            if not dr: continue
            basis=dr['basis']; physical+=dr['physical']; adj+=dr['adjustments']; count_sale+=dr['count_sale']; stock_gain+=dr['stock_gain']; adjustment_excess+=dr['adjustment_excess']; complete+=1
            if dr['pos_ready']:
                pos_sale+=float(dr['pos_sale'] or 0); pos_complete+=1
        ready=complete>0 and pos_complete==complete; diff=(count_sale-pos_sale) if ready else None
        state_code,state_label,diff_text=_difference_state(p,diff,complete>0,pos_ready=ready)
        if basis=='bottle' and complete>0 and stock_gain<=0 and adjustment_excess<=0:
            state_code,state_label,diff_text=('PENDING','⚠ Falta ml para POS','—')
        if stock_gain>0:
            state_code,state_label=('ALERT','🔴 Revisar entradas/conteo')
        elif adjustment_excess>0:
            state_code,state_label=('REVIEW','🟡 Revisar ajustes')
        rows.append({'Producto':p['name'],'Categoría':p['category'],'Consumo real':physical,'Consumo físico':physical,'Ajustes':adj,
                     'Venta por conteo':count_sale,'Ventas POS':pos_sale,'Consumo esperado':pos_sale,'Diferencia':diff,'Días completos':complete,
                     'Días POS completos':pos_complete,'Estado':state_label,
                     'Incidencia física':physical_issue_text_basis(p,stock_gain,adjustment_excess,basis),
                     '_stock_gain':stock_gain,'_adjustment_excess':adjustment_excess,'_state':state_code,'_p':p,'_basis':basis,'_diff_text':diff_text})
    return rows

def cocktail_sales_summary(d1,d2):
    rows=q("""SELECT c.id,c.name,COALESCE(SUM(CASE WHEN ps.sale_type='Cóctel' THEN ps.quantity ELSE 0 END),0) sold,
                     COALESCE((SELECT SUM(r.oz_qty) FROM recipes r WHERE r.cocktail_id=c.id),0) recipe_oz
              FROM cocktails c
              LEFT JOIN pos_sales ps ON ps.cocktail_id=c.id AND ps.sale_date BETWEEN ? AND ?
              WHERE c.active=1 GROUP BY c.id,c.name ORDER BY sold DESC,c.name""",(d1.isoformat(),d2.isoformat()))
    out=[]
    for r in rows:
        sold=float(r['sold'] or 0); recipe_oz=float(r['recipe_oz'] or 0)
        if recipe_oz<=0 and sold>0: code,label='ALERT','🔴 Sin receta'
        elif recipe_oz<=0: code,label='PENDING','⏳ Receta pendiente'
        else: code,label='OK','🟢 OK'
        out.append({'Cóctel':r['name'],'Vendidos':sold,'Oz licor / cóctel':recipe_oz if recipe_oz>0 else None,
                    'Consumo teórico':sold*recipe_oz,'Estado':label,'_state':code})
    return out

def shot_sales_summary(d1,d2):
    rows=q("""SELECT p.name,SUM(ps.quantity) sold,
                     SUM(ps.quantity*COALESCE(ps.oz_per_unit,0)) total_oz
              FROM pos_sales ps JOIN products p ON p.id=ps.product_id
              WHERE ps.sale_type='Shot' AND ps.sale_date BETWEEN ? AND ?
              GROUP BY p.id,p.name ORDER BY sold DESC,p.name""",(d1.isoformat(),d2.isoformat()))
    out=[]
    for r in rows:
        sold=float(r['sold'] or 0); total=float(r['total_oz'] or 0)
        out.append({'Licor':r['name'],'Shots vendidos':sold,'Oz / shot promedio':(total/sold if sold else 0),
                    'Consumo teórico':total,'Estado':'🟢 OK','_state':'OK'})
    return out

def beer_sales_summary(d1,d2):
    rows=q("""SELECT p.name,SUM(ps.quantity) sold FROM pos_sales ps JOIN products p ON p.id=ps.product_id
              WHERE ps.sale_type='Cerveza' AND ps.sale_date BETWEEN ? AND ?
              GROUP BY p.id,p.name ORDER BY sold DESC,p.name""",(d1.isoformat(),d2.isoformat()))
    return [{'Cerveza':r['name'],'Vendidas':float(r['sold'] or 0)} for r in rows]

def _status_filter(rows,status):
    if status=='Todos': return rows
    if status=='Con alerta': return [r for r in rows if r.get('_state') in ('ALERT','REVIEW')]
    if status=='Pendientes': return [r for r in rows if r.get('_state')=='PENDING']
    if status=='OK': return [r for r in rows if r.get('_state')=='OK']
    return rows


def _pdf_clean(value):
    """Texto seguro para las fuentes base de ReportLab y sin emojis de la interfaz."""
    if value is None:
        return "-"
    txt=str(value)
    replacements={
        '—':'-', '–':'-', '·':' - ', '✅':'', '🟢':'', '🟡':'', '🔴':'', '⏳':'', '⚠️':'', '⚠':'',
        '↑':'', '↓':'', '→':'->', '←':'<-'
    }
    for a,b in replacements.items(): txt=txt.replace(a,b)
    return re.sub(r'\s+',' ',txt).strip() or '-'


def _pdf_state_label(code):
    return {'OK':'OK','REVIEW':'REVISAR','ALERT':'ALERTA','PENDING':'PENDIENTE'}.get(code,_pdf_clean(code).upper())


def _report_inventory_status(d1,d2):
    dates=[r['session_date'] for r in q("SELECT DISTINCT session_date FROM inventory_sessions WHERE session_type='CLOSING' AND session_date BETWEEN ? AND ? AND COALESCE(inventory_cycle,'DAILY')='DAILY' ORDER BY session_date",(d1.isoformat(),d2.isoformat()))]
    active=len(dates);complete=0
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    for ds in dates:
        # A comparable day requires a current close and at least one previous close baseline.
        comparable=False
        for p in inventory_products('DAILY'):
            dr=day_product_reconciliation(ds,p,bar)
            if dr and not dr.get('baseline_missing'):
                comparable=True;break
        if comparable:complete+=1
    if active==0:state='SIN CIERRE FISICO'
    elif complete==active:state='COMPLETO' if active==1 else f'COMPLETO - {complete} CIERRES COMPARABLES'
    else:state=f'PARCIAL - {complete}/{active} CIERRES CON BASE ANTERIOR'
    counted=one("""SELECT COUNT(DISTINCT ic.product_id) n
                   FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                   WHERE s.session_type='CLOSING' AND s.session_date BETWEEN ? AND ?""",(d1.isoformat(),d2.isoformat()))['n']
    latest=one("""SELECT s.session_date,s.session_type,s.created_at,u.name employee,COUNT(ic.id) item_count
                  FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                  LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                  WHERE s.session_type='CLOSING' AND s.session_date BETWEEN ? AND ?
                  GROUP BY s.id ORDER BY s.created_at DESC,s.id DESC LIMIT 1""",(d1.isoformat(),d2.isoformat()))
    return {'state':state,'active_days':active,'complete_days':complete,'products_counted':int(counted or 0),'latest':latest}

def _report_accuracy(perf_rows):
    vals=[]
    for r in perf_rows:
        if r['Días completos']<=0 or r['Diferencia'] is None: continue
        base=abs(float(r.get('Venta por conteo',0) or 0)); diff=abs(float(r['Diferencia'] or 0))
        if base<=0:
            if diff<=1e-9: vals.append(100.0)
            continue
        vals.append(max(0.0,min(100.0,(1.0-diff/base)*100.0)))
    return sum(vals)/len(vals) if vals else None

def _report_difference_cost(perf_row):
    p=perf_row['_p']; cost=p['unit_cost']
    if cost is None or perf_row['Diferencia'] is None: return None
    diff=abs(float(perf_row['Diferencia'] or 0))
    if p['category']=='Cerveza': return diff*float(cost)
    boz=bottle_oz(p)
    return (diff/boz*float(cost)) if boz else None


def _report_replenishment(perf_rows):
    bar_id=one("SELECT id FROM locations WHERE name='Bar'")['id']
    wh_id=one("SELECT id FROM locations WHERE name='Bodega'")['id']
    safety=float(setting('safety_stock_pct','15'))/100
    rows=[]
    for r in perf_rows:
        if r['Días completos']<=0: continue
        p=r['_p']; basis=r.get('_basis','unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle'))
        weekly=max(float(r['Consumo real'] or 0),0)/max(r['Días completos'],1)*7
        target=weekly*(1+safety)
        sb,sbb=current_stock_basis(p,bar_id); sw,swb=current_stock_basis(p,wh_id)
        if sbb!=basis or swb!=basis:
            continue
        stock=max(sb+sw,0); need=max(target-stock,0)
        if need<=0: continue
        if p['category']=='Cerveza':
            buy=math.ceil(need); action=f'{buy} unidades'
        elif basis=='bottle':
            buy=math.ceil(need); action=f'{buy} botellas'
        else:
            boz=bottle_oz(p); buy=(math.ceil(need/boz) if boz else None); action=(f'{buy} botellas' if buy is not None else 'Falta presentación ml')
        rows.append({'Producto':p['name'],'Categoría':p['category'],'Necesidad':need,'Stock':stock,
                     'Comprar':action,'_p':p,'_buy':buy,'_basis':basis})
    rows.sort(key=lambda x:(0 if x['_buy'] is None else -x['_buy'],x['Producto']))
    return rows


def _report_observations(perf, inv_status, cocktails, shots, beers, replenishment, total_cost, missing_costs):
    notes=[]
    comparable=[r for r in perf if r['Días completos']>0 and r['Diferencia'] is not None]
    alerts=[r for r in comparable if r['_state']=='ALERT']
    reviews=[r for r in comparable if r['_state']=='REVIEW']
    if inv_status['active_days']==0:
        notes.append('No hay inventario físico registrado en el periodo. El reporte muestra únicamente la información comercial disponible.')
    elif inv_status['complete_days']==0:
        notes.append('No existen cierres con un cierre anterior comparable. El consumo físico, las diferencias y la exactitud permanecen pendientes para evitar conclusiones falsas.')
    elif inv_status['complete_days']<inv_status['active_days']:
        notes.append(f"El periodo contiene {inv_status['complete_days']} cierre(s) comparable(s) de {inv_status['active_days']} cierre(s) con actividad. Las métricas físicas usan solo periodos comparables.")
    else:
        notes.append(f"El periodo contiene {inv_status['complete_days']} cierre(s) con cierre anterior comparable.")
    pending_ml=[r for r in perf if r.get('Días completos',0)>0 and r.get('_basis')=='bottle']
    if pending_ml:
        notes.append(f"Hay {len(pending_ml)} licor(es) con conteo físico conservado en botellas equivalentes y presentación ml pendiente. Sus cantidades no se pierden; la comparación con POS/recetas en oz se activará al completar los ml.")
    pending_pos=[r for r in perf if r.get('Días completos',0)>r.get('Días POS completos',0) and r.get('_basis')!='bottle']
    if pending_pos:
        notes.append(f"Hay {len(pending_pos)} producto(s) con inventario físico comparable pero POS aún pendiente de confirmar; no generan alerta hasta completar el POS.")
    if alerts or reviews:
        notes.append(f"Se identificaron {len(alerts)} alerta(s) crítica(s) y {len(reviews)} producto(s) para revisar al comparar venta por conteo contra POS.")
    elif comparable:
        notes.append('No se detectaron diferencias por encima de las tolerancias al comparar venta por conteo contra POS.')
    recipe_alerts=[r for r in cocktails if r['Vendidos']>0 and r['_state']=='ALERT']
    if recipe_alerts:
        notes.append(f"Hay {len(recipe_alerts)} cóctel(es) con ventas y sin receta completa; su consumo teórico de licor no puede explicarse correctamente.")
    if replenishment:
        notes.append(f"El cálculo de abastecimiento sugiere reponer {len(replenishment)} producto(s) según consumo reciente, stock disponible y margen de seguridad.")
    if total_cost is not None and total_cost>0:
        cost_note=f"El costo estimado conocido de las diferencias es ${total_cost:,.2f}."
        if missing_costs: cost_note += f" {missing_costs} producto(s) con diferencia no tienen costo configurado."
        notes.append(cost_note)
    elif missing_costs:
        notes.append(f"No es posible valorar completamente las diferencias: {missing_costs} producto(s) con diferencia no tienen costo configurado.")
    if not any(r['Vendidos']>0 for r in cocktails) and not shots and not beers:
        notes.append('No hay ventas POS registradas en el periodo seleccionado.')
    return notes[:6]


def build_executive_report_pdf(d1,d2):
    """Genera un PDF gerencial: resumen ejecutivo primero y detalle operativo después."""
    perf=period_inventory_performance(d1,d2)
    comparable=[r for r in perf if r['Días completos']>0 and r['Diferencia'] is not None]
    cocktails=cocktail_sales_summary(d1,d2)
    shots=shot_sales_summary(d1,d2)
    beers=beer_sales_summary(d1,d2)
    inv_status=_report_inventory_status(d1,d2)
    replenishment=_report_replenishment(perf)

    physical_rows=[r for r in perf if r['Días completos']>0]
    liquor_oz_rows=[r for r in physical_rows if r['Categoría']=='Licor' and r.get('_basis')=='oz']
    liquor_bottle_rows=[r for r in physical_rows if r['Categoría']=='Licor' and r.get('_basis')=='bottle']
    liquor_rows=[r for r in comparable if r['Categoría']=='Licor']
    beer_rows=[r for r in comparable if r['Categoría']=='Cerveza']
    liquor_real=sum(float(r['Consumo físico'] or 0) for r in liquor_oz_rows)
    liquor_real_bottles=sum(float(r['Consumo físico'] or 0) for r in liquor_bottle_rows)
    liquor_count_sale=sum(float(r['Venta por conteo'] or 0) for r in liquor_oz_rows)
    liquor_count_sale_bottles=sum(float(r['Venta por conteo'] or 0) for r in liquor_bottle_rows)
    liquor_pos=sum(float(r['Ventas POS'] or 0) for r in liquor_rows)
    beer_real=sum(float(r['Consumo físico'] or 0) for r in beer_rows)
    beer_count_sale=sum(float(r['Venta por conteo'] or 0) for r in beer_rows)
    beer_expected=sum(float(r['Ventas POS'] or 0) for r in beer_rows)
    cocktail_sold=sum(float(r['Vendidos'] or 0) for r in cocktails)
    cocktail_oz=sum(float(r['Consumo teórico'] or 0) for r in cocktails)
    shot_sold=sum(float(r['Shots vendidos'] or 0) for r in shots)
    shot_oz=sum(float(r['Consumo teórico'] or 0) for r in shots)
    beer_pos=sum(float(r['Vendidas'] or 0) for r in beers)
    accuracy=_report_accuracy(perf)
    review_count=sum(1 for r in comparable if r['_state'] in ('REVIEW','ALERT'))
    critical_count=sum(1 for r in comparable if r['_state']=='ALERT')

    cost_values=[]; missing_costs=0
    for r in comparable:
        if r['_state'] not in ('REVIEW','ALERT'): continue
        cv=_report_difference_cost(r)
        if cv is None: missing_costs+=1
        else: cost_values.append(cv)
    total_cost=sum(cost_values) if cost_values else (0.0 if review_count and not missing_costs else None)

    def severity(r):
        tol=float(setting('tolerance_beer','1')) if r['Categoría']=='Cerveza' else float(setting('tolerance_liquor','1'))
        return abs(float(r['Diferencia'] or 0))/max(tol,1e-9)
    attention=sorted([r for r in comparable if r['_state'] in ('REVIEW','ALERT')],key=severity,reverse=True)
    largest=attention[0] if attention else None

    buf=io.BytesIO()
    page_w,page_h=landscape(letter)
    doc=SimpleDocTemplate(buf,pagesize=landscape(letter),leftMargin=26,rightMargin=26,topMargin=28,bottomMargin=28,
                          title=f"La Ramona - Reporte Ejecutivo {d1} a {d2}",author="Inventario La Ramona")
    styles=getSampleStyleSheet()
    title_style=ParagraphStyle('RamonaTitle',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=20,leading=23,textColor=colors.HexColor('#20252b'),spaceAfter=4)
    subtitle_style=ParagraphStyle('RamonaSub',parent=styles['Normal'],fontName='Helvetica',fontSize=9,leading=12,textColor=colors.HexColor('#626b75'))
    section_style=ParagraphStyle('RamonaSection',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=11.5,leading=14,textColor=colors.HexColor('#d94d35'),spaceBefore=8,spaceAfter=5)
    small_style=ParagraphStyle('RamonaSmall',parent=styles['Normal'],fontName='Helvetica',fontSize=7.3,leading=9.5,textColor=colors.HexColor('#32373d'))
    body_style=ParagraphStyle('RamonaBody',parent=styles['Normal'],fontName='Helvetica',fontSize=8.5,leading=11,textColor=colors.HexColor('#32373d'))
    center_style=ParagraphStyle('RamonaCenter',parent=body_style,alignment=TA_CENTER)
    card_label=ParagraphStyle('CardLabel',parent=small_style,fontName='Helvetica-Bold',fontSize=7.2,textColor=colors.HexColor('#6a737d'),alignment=TA_CENTER)
    card_value=ParagraphStyle('CardValue',parent=body_style,fontName='Helvetica-Bold',fontSize=13,leading=15,textColor=colors.HexColor('#1b1f23'),alignment=TA_CENTER)

    def P(txt,style=body_style): return Paragraph(_pdf_clean(txt),style)
    def metric_cell(label,value):
        return [Paragraph(_pdf_clean(label),card_label),Spacer(1,2),Paragraph(_pdf_clean(value),card_value)]
    def state_text(r): return _pdf_state_label(r.get('_state'))
    def diff_text(r):
        if r.get('Diferencia') is None: return '-'
        return dual_qty_text(r['_p'],r['Diferencia'],signed=True).replace('⚠','')
    def cost_text(r):
        v=_report_difference_cost(r)
        return f"${v:,.2f}" if v is not None else '-'
    def accuracy_text(r):
        real=abs(float(r.get('Venta por conteo',0) or 0)); diff=abs(float(r['Diferencia'] or 0)) if r['Diferencia'] is not None else None
        if not real or diff is None: return '-'
        return f"{max(0.0,min(100.0,(1-diff/real)*100)):.1f}%"

    def table_style(header_bg='#252a31',font_size=7.2):
        return TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor(header_bg)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),
            ('FONTSIZE',(0,0),(-1,-1),font_size),('LEADING',(0,0),(-1,-1),font_size+2),
            ('GRID',(0,0),(-1,-1),0.25,colors.HexColor('#d7dce1')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f8fa')]),
            ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ])

    def page_footer(canvas,doc_obj):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d8dde3')); canvas.setLineWidth(.5)
        canvas.line(26,20,page_w-26,20)
        canvas.setFillColor(colors.HexColor('#727b86')); canvas.setFont('Helvetica',7)
        canvas.drawString(26,9,'La Ramona - Reporte Ejecutivo de Inventario')
        canvas.drawRightString(page_w-26,9,f'Página {doc_obj.page}')
        canvas.restoreState()

    story=[]
    # Cabecera
    header=[]
    if os.path.exists(LOGO_PATH):
        try:
            logo=RLImage(LOGO_PATH)
            ratio=(float(logo.imageHeight)/float(logo.imageWidth)) if logo.imageWidth else .46
            logo.drawWidth=1.55*inch; logo.drawHeight=logo.drawWidth*ratio
            header.append(logo)
        except Exception: header.append(P('LA RAMONA',title_style))
    else: header.append(P('LA RAMONA',title_style))
    head_text=[Paragraph('REPORTE EJECUTIVO DE INVENTARIO',title_style),
               Paragraph(f"Periodo: {d1.strftime('%d/%m/%Y')} al {d2.strftime('%d/%m/%Y')} | Generado: {local_now().strftime('%d/%m/%Y %I:%M %p')}",subtitle_style)]
    ht=Table([[header[0],head_text]],colWidths=[1.75*inch,8.1*inch])
    ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    story += [ht,Spacer(1,5)]

    latest=inv_status['latest']
    latest_txt='Sin registros'
    if latest:
        kind='Apertura' if latest['session_type']=='OPENING' else 'Cierre'
        latest_txt=f"{kind} por {latest['employee'] or 'Usuario'} - {format_local_datetime(latest['created_at'],'%d/%m/%Y %I:%M %p')} - {int(latest['item_count'] or 0)} productos"
    status_tbl=Table([[P('Estado del periodo',small_style),P(inv_status['state'],ParagraphStyle('st',parent=body_style,fontName='Helvetica-Bold',textColor=colors.HexColor('#d94d35'))),
                       P('Último registro',small_style),P(latest_txt,small_style)]],colWidths=[1.05*inch,2.15*inch,1.0*inch,5.6*inch])
    status_tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fff5ef')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#efc2ad')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story += [status_tbl,Spacer(1,7),Paragraph('Indicadores clave',section_style)]

    physical_available=inv_status['complete_days']>0
    def liquor_mix_text(oz_value,bottle_value,empty='Pendiente'):
        parts=[]
        if abs(float(oz_value or 0))>1e-9: parts.append(f'{float(oz_value):.2f} oz')
        if abs(float(bottle_value or 0))>1e-9: parts.append(f'{float(bottle_value):.2f} bot (ml pend.)')
        return ' + '.join(parts) if parts else empty
    largest_txt='Sin diferencias'
    if largest:
        largest_txt=f"{largest['Producto']} ({diff_text(largest)})"
    kpis=[
        ('Venta por conteo licor',liquor_mix_text(liquor_count_sale,liquor_count_sale_bottles) if physical_available else 'Pendiente'),
        ('Venta por conteo cerveza',f'{beer_count_sale:.0f} unid' if physical_available and beer_rows else 'Pendiente'),
        ('Cócteles vendidos',f'{cocktail_sold:.0f}'),
        ('Shots vendidos',f'{shot_sold:.0f}'),
        ('Exactitud promedio',f'{accuracy:.1f}%' if accuracy is not None else 'Sin datos'),
        ('Productos con diferencia',str(review_count) if physical_available else 'Pendiente'),
        ('Alertas críticas',str(critical_count) if physical_available else 'Pendiente'),
        ('Costo estimado diferencias',f'${total_cost:,.2f}' if total_cost is not None else 'Sin datos'),
    ]
    card_rows=[]
    for i in range(0,len(kpis),4):
        row=[]
        for label,value in kpis[i:i+4]:
            nested=Table([[Paragraph(_pdf_clean(label),card_label)],[Paragraph(_pdf_clean(value),card_value)]],colWidths=[2.42*inch])
            nested.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f5f6f8')),('BOX',(0,0),(-1,-1),.45,colors.HexColor('#d9dee4')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            row.append(nested)
        card_rows.append(row)
    kt=Table(card_rows,colWidths=[2.48*inch]*4)
    kt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    story += [kt,Spacer(1,6)]

    # Resumen comercial / consumo
    story.append(Paragraph('Resumen comercial y de consumo',section_style))
    summary_data=[
        [P('Indicador',small_style),P('Resultado',small_style),P('Indicador',small_style),P('Resultado',small_style)],
        [P('Salida física de licor'),P(liquor_mix_text(liquor_real,liquor_real_bottles,'Pendiente de cierre') if physical_available else 'Pendiente de cierre'),P('Venta conteo / POS-recetas licor'),P((liquor_mix_text(liquor_count_sale,liquor_count_sale_bottles)+' / '+(f'{liquor_pos:.2f} oz' if liquor_rows else 'POS pendiente / ml pendiente')) if physical_available else 'Pendiente')],
        [P('Salida física de cerveza'),P(f'{beer_real:.0f} unidades' if physical_available and beer_rows else 'Pendiente de cierre'),P('Venta por conteo / POS cerveza'),P(f'{beer_count_sale:.0f} / {beer_pos:.0f}' if physical_available and beer_rows else 'Pendiente')],
        [P('Cócteles vendidos'),P(f'{cocktail_sold:.0f}'),P('Licor teórico en cócteles'),P(f'{cocktail_oz:.2f} oz')],
        [P('Shots vendidos'),P(f'{shot_sold:.0f}'),P('Licor teórico en shots'),P(f'{shot_oz:.2f} oz')],
        [P('Productos contados'),P(f"{inv_status['products_counted']}"),P('Mayor diferencia'),P(largest_txt)],
        [P('Productos con compra sugerida'),P(f'{len(replenishment)}'),P('Días comparables'),P(f"{inv_status['complete_days']}")],
    ]
    stbl=Table(summary_data,colWidths=[1.8*inch,2.0*inch,1.9*inch,4.0*inch],repeatRows=1)
    stbl.setStyle(table_style('#454b54',7.2)); story += [stbl,Spacer(1,5)]

    story.append(Paragraph('Lectura gerencial',section_style))
    observations=_report_observations(perf,inv_status,cocktails,shots,beers,replenishment,total_cost,missing_costs)
    for note in observations:
        story.append(Paragraph(f"• {_pdf_clean(note)}",body_style))

    # -------- detalle --------
    story += [PageBreak(),Paragraph('Detalle gerencial y operativo',title_style),Paragraph('Productos con atención prioritaria al comparar venta por conteo contra POS.',subtitle_style),Spacer(1,7)]
    story.append(Paragraph('Productos que requieren atención',section_style))
    if attention:
        att=[['Producto','Tipo','Físico','Ajustes','Venta conteo','POS/recetas','Diferencia','Incidencia','Estado']]
        for r in attention[:10]:
            p=r['_p']
            att.append([_pdf_clean(r['Producto']),r['Categoría'],_pdf_clean(basis_qty_text(p,r['Consumo físico'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),_pdf_clean(basis_qty_text(p,r['Ajustes'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),_pdf_clean(basis_qty_text(p,r['Venta por conteo'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),_pdf_clean(basis_qty_text(p,r['Ventas POS'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),diff_text(r),_pdf_clean(r.get('Incidencia física','—')),state_text(r)])
        t=Table(att,colWidths=[1.15*inch,.50*inch,1.05*inch,.95*inch,1.15*inch,1.15*inch,.95*inch,1.55*inch,.90*inch],repeatRows=1)
        t.setStyle(table_style('#9f3f32',6.8)); story.append(t)
    else:
        msg='No hay diferencias calculables todavía.' if not physical_available else 'No hay productos por encima de las tolerancias configuradas.'
        story.append(P(msg))

    story += [Spacer(1,8),Paragraph('Detalle de inventario comparable',section_style),Paragraph('La diferencia = venta por conteo - POS. Positiva: salida física no explicada por POS. Negativa: POS registra más ventas que las explicadas por el conteo. Ambas se revisan si superan tolerancia.',subtitle_style),Spacer(1,5)]
    if comparable:
        detail=[['Producto','Tipo','Físico','Ajustes','Venta conteo','POS/recetas','Diferencia','Incidencia','Exact.','Estado','Días']]
        for r in sorted(comparable,key=lambda x:(x['Categoría'],x['Producto'])):
            p=r['_p']
            detail.append([_pdf_clean(r['Producto']),r['Categoría'],_pdf_clean(basis_qty_text(p,r['Consumo físico'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),_pdf_clean(basis_qty_text(p,r['Ajustes'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),_pdf_clean(basis_qty_text(p,r['Venta por conteo'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),_pdf_clean(basis_qty_text(p,r['Ventas POS'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))),diff_text(r),_pdf_clean(r.get('Incidencia física','—')),accuracy_text(r),state_text(r),str(r['Días completos'])])
        dt=Table(detail,colWidths=[.95*inch,.45*inch,.95*inch,.85*inch,1.05*inch,1.05*inch,.85*inch,1.35*inch,.50*inch,.70*inch,.30*inch],repeatRows=1)
        dt.setStyle(table_style('#252a31',6.6)); story.append(dt)
    else:
        story.append(P('No hay productos con cierres consecutivos + POS completo para comparar en el periodo seleccionado.'))

    pending_ml_rows=[r for r in physical_rows if r['Categoría']=='Licor' and r.get('_basis')=='bottle']
    if pending_ml_rows:
        story += [Spacer(1,8),Paragraph('Licores contados con presentación ml pendiente',section_style),
                  Paragraph('Estos conteos físicos se conservan en botellas equivalentes. No se comparan contra recetas/POS en oz hasta registrar la presentación en ml.',subtitle_style),Spacer(1,4)]
        pml=[['Producto','Salida física','Ajustes','Venta por conteo','Estado']]
        for r in pending_ml_rows:
            pml.append([r['Producto'],basis_qty_text(r['_p'],r['Consumo físico'],'bottle'),basis_qty_text(r['_p'],r['Ajustes'],'bottle'),basis_qty_text(r['_p'],r['Venta por conteo'],'bottle'),_pdf_clean(r['Estado'])])
        pmt=Table(pml,colWidths=[3.0*inch,1.7*inch,1.5*inch,1.8*inch,2.0*inch],repeatRows=1); pmt.setStyle(table_style('#7c4a3b',7)); story.append(pmt)

    story += [Spacer(1,9),Paragraph('Ventas POS y consumo teórico',section_style)]
    sales_summary=[['Categoría','Ventas','Consumo teórico / referencia','Producto más vendido']]
    cocktail_top=next((r for r in cocktails if r['Vendidos']>0),None)
    shot_top=shots[0] if shots else None
    beer_top=beers[0] if beers else None
    sales_summary.append(['Cócteles',f'{cocktail_sold:.0f}',f'{cocktail_oz:.2f} oz de licor',cocktail_top['Cóctel'] if cocktail_top else '-'])
    sales_summary.append(['Shots',f'{shot_sold:.0f}',f'{shot_oz:.2f} oz de licor',shot_top['Licor'] if shot_top else '-'])
    sales_summary.append(['Cervezas',f'{beer_pos:.0f}','Unidades POS',beer_top['Cerveza'] if beer_top else '-'])
    sat=Table(sales_summary,colWidths=[1.4*inch,1.0*inch,2.0*inch,5.25*inch],repeatRows=1); sat.setStyle(table_style('#454b54',7.3)); story.append(sat)

    if any(r['Vendidos']>0 for r in cocktails):
        story += [Spacer(1,7),Paragraph('Cócteles vendidos',section_style)]
        ctbl=[['Cóctel','Vendidos','Oz licor/receta','Consumo teórico','Estado']]
        for r in [x for x in cocktails if x['Vendidos']>0][:25]:
            ctbl.append([r['Cóctel'],f"{r['Vendidos']:.0f}",f"{r['Oz licor / cóctel']:.2f}" if r['Oz licor / cóctel'] is not None else '-',f"{r['Consumo teórico']:.2f} oz",_pdf_state_label(r['_state'])])
        ct=Table(ctbl[:13],colWidths=[2.8*inch,1.0*inch,1.25*inch,1.35*inch,3.25*inch],repeatRows=1); ct.setStyle(table_style('#7c4a3b',7));
        story[-1:]=[KeepTogether([Paragraph('Cócteles vendidos',section_style),ct])]

    if shots:
        story += [Spacer(1,7),Paragraph('Shots vendidos',section_style)]
        sht=[['Licor','Shots','Oz promedio','Consumo teórico']]
        for r in shots[:25]: sht.append([r['Licor'],f"{r['Shots vendidos']:.0f}",f"{r['Oz / shot promedio']:.2f}",f"{r['Consumo teórico']:.2f} oz"])
        sh=Table(sht[:13],colWidths=[3.2*inch,1.2*inch,1.4*inch,3.8*inch],repeatRows=1); sh.setStyle(table_style('#7c4a3b',7));
        story[-1:]=[KeepTogether([Paragraph('Shots vendidos',section_style),sh])]

    if beers:
        story += [Spacer(1,7),Paragraph('Cervezas vendidas',section_style)]
        bt=[['Cerveza','Unidades vendidas']]+[[r['Cerveza'],f"{r['Vendidas']:.0f}"] for r in beers[:30]]
        btb=Table(bt[:11],colWidths=[5.5*inch,4.1*inch],repeatRows=1); btb.setStyle(table_style('#7c4a3b',7));
        story[-1:]=[KeepTogether([Paragraph('Cervezas vendidas',section_style),btb])]

    story += [Spacer(1,12),Paragraph('Abastecimiento y trazabilidad',title_style),Paragraph('Resumen de reposición sugerida y sesiones de inventario del periodo.',subtitle_style),Spacer(1,8)]
    story.append(Paragraph('Abastecimiento sugerido',section_style))
    if replenishment:
        rt=[['Producto','Tipo','Stock actual','Necesidad estimada','Compra sugerida']]
        for r in replenishment[:30]:
            p=r['_p']
            stock=basis_qty_text(p,r['Stock'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))
            need=basis_qty_text(p,r['Necesidad'],r.get('_basis','unit' if p['category']=='Cerveza' else 'oz'))
            rt.append([r['Producto'],r['Categoría'],stock,need,r['Comprar']])
        rtb=Table(rt,colWidths=[2.4*inch,.8*inch,1.9*inch,1.9*inch,2.6*inch],repeatRows=1); rtb.setStyle(table_style('#355c4d',7)); story.append(rtb)
    else:
        story.append(P('No hay una recomendación de compra calculable con los días completos del periodo.'))

    story += [PageBreak(),Paragraph('Trazabilidad operativa',title_style),Paragraph('Sesiones de inventario y movimientos registrados dentro del periodo seleccionado.',subtitle_style),Spacer(1,8),Paragraph('Sesiones de inventario',section_style)]
    sessions=q("""SELECT s.session_date,s.session_type,s.inventory_cycle,s.created_at,u.name employee,COUNT(ic.id) item_count
                  FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                  LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                  WHERE s.session_date BETWEEN ? AND ?
                  GROUP BY s.id ORDER BY s.session_date,s.created_at""",(d1.isoformat(),d2.isoformat()))
    if sessions:
        it=[['Fecha','Tipo','Ciclo','Empleado','Hora local','Productos']]
        for r in sessions:
            it.append([r['session_date'],'Apertura' if r['session_type']=='OPENING' else 'Cierre','Semanal' if r['inventory_cycle']=='WEEKLY' else 'Diario',r['employee'] or 'Usuario',format_local_time(r['created_at']),str(int(r['item_count'] or 0))])
        itt=Table(it,colWidths=[1.1*inch,1.0*inch,1.0*inch,2.2*inch,1.3*inch,3.0*inch],repeatRows=1); itt.setStyle(table_style('#454b54',7)); story.append(itt)
    else:
        story.append(P('No hay sesiones de inventario en el periodo.'))

    story += [Spacer(1,8),Paragraph('Movimientos registrados',section_style)]
    movements=q("""SELECT m.movement_date,m.movement_type,p.name product,c.name category,m.qty_base,m.qty_bottle_equiv,u.name employee,m.created_at
                   FROM movements m JOIN products p ON p.id=m.product_id JOIN categories c ON c.id=p.category_id
                   LEFT JOIN users u ON u.id=m.user_id
                   WHERE m.movement_date BETWEEN ? AND ? ORDER BY m.created_at DESC LIMIT 50""",(d1.isoformat(),d2.isoformat()))
    if movements:
        labels={'SUPPLIER':'Proveedor','TRANSFER':'Traslado','PRUEBA':'Prueba','DESPERDICIO':'Desperdicio','CORTESIA':'Cortesía','ROTURA':'Rotura / botella quebrada'}
        mt=[['Fecha','Movimiento','Producto','Cantidad','Empleado','Hora']]
        for r in movements:
            if r['category']=='Cerveza': qty=f"{float(r['qty_base'] or 0):.0f} unid"
            elif r['qty_bottle_equiv'] is not None: qty=f"{float(r['qty_bottle_equiv']):.2f} bot / {float(r['qty_base'] or 0):.2f} oz"
            else: qty=f"{float(r['qty_base'] or 0):.2f} oz"
            mt.append([r['movement_date'],labels.get(r['movement_type'],r['movement_type']),r['product'],qty,r['employee'] or 'Usuario',format_local_time(r['created_at'])])
        mtt=Table(mt,colWidths=[.9*inch,1.1*inch,2.3*inch,1.5*inch,2.1*inch,1.7*inch],repeatRows=1); mtt.setStyle(table_style('#454b54',6.8)); story.append(mtt)
    else:
        story.append(P('No hay movimientos registrados en el periodo.'))

    doc.build(story,onFirstPage=page_footer,onLaterPages=page_footer)
    buf.seek(0)
    return buf

# --------------------------- Google authentication ---------------------------
def secret_value(section, key, default=""):
    try:
        return str(st.secrets[section][key]).strip()
    except Exception:
        return default

def normalized_email(v): return (v or "").strip().lower()

def is_developer_user(user):
    """Identifica la cuenta Developer/Owner configurada en Streamlit Secrets."""
    dev_email=normalized_email(secret_value("app","bootstrap_admin_email"))
    return bool(dev_email and user and normalized_email(user.get("email")) == dev_email)

def can_download_executive_report(user):
    """Developer/Owner siempre puede descargar; otros usuarios requieren autorización individual."""
    if is_developer_user(user):
        return True
    return bool(user and int(user.get("active",0) or 0)==1 and int(user.get("report_access",0) or 0)==1)

def google_identity():
    if not st.user.is_logged_in:
        return None
    try:
        return {"email": normalized_email(st.user.email), "name": str(st.user.name or "").strip()}
    except Exception:
        return None

def bootstrap_admin(identity):
    """Autoriza automáticamente solo el correo ADMIN configurado en Secrets.
    Esto permite arrancar V0.3 sin dejar un registro público ni un PIN compartido."""
    admin_email=normalized_email(secret_value("app","bootstrap_admin_email"))
    if not identity or not admin_email or identity["email"] != admin_email:
        return
    u=one("SELECT * FROM users WHERE lower(email)=?",(admin_email,))
    if u:
        ex("UPDATE users SET active=1,role='ADMIN',report_access=1,last_login_at=? WHERE id=?",(now_iso(),u['id']))
        return
    legacy=one("SELECT * FROM users WHERE name='Admin' AND (email IS NULL OR email='') ORDER BY id LIMIT 1")
    if legacy:
        ex("UPDATE users SET email=?,name=?,role='ADMIN',active=1,report_access=1,last_login_at=?,created_at=COALESCE(created_at,?) WHERE id=?",
           (admin_email,identity['name'] or 'Admin',now_iso(),now_iso(),legacy['id']))
    else:
        ex("INSERT INTO users(name,pin_hash,email,role,active,report_access,last_login_at,created_at) VALUES(?,?,?,?,1,1,?,?)",
           (identity['name'] or admin_email,'',admin_email,'ADMIN',now_iso(),now_iso()))

def login_screen():
    st.markdown('<div class="ramona-login-wrap">', unsafe_allow_html=True)
    st.image(LOGO_PATH, width=320)
    st.markdown("## Inventario La Ramona")
    st.caption(f"Control de inventario · V{APP_VERSION} · Acceso seguro con Google")
    st.write("Inicia sesión con la cuenta de Google autorizada por el administrador.")
    st.button("Continuar con Google",type="primary",width="stretch",on_click=st.login)
    st.caption("Tener el enlace de la aplicación no concede acceso. El correo debe estar autorizado y activo.")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.user.is_logged_in:
    login_screen(); st.stop()

identity=google_identity()
bootstrap_admin(identity)
user_row=one("SELECT * FROM users WHERE lower(email)=?",(identity['email'],)) if identity else None
if not user_row or not user_row['active']:
    page_header("Acceso no autorizado", "La cuenta actual no tiene permisos activos para usar el sistema.")
    if identity:
        st.write(f"La cuenta **{identity['email']}** no tiene acceso activo a Inventario La Ramona.")
    st.caption("Solicita al administrador que autorice o reactive este correo.")
    st.button("Cerrar sesión",width="stretch",on_click=st.logout)
    st.stop()

user=dict(user_row)
ex("UPDATE users SET last_login_at=? WHERE id=?",(now_iso(),user['id']),do_backup=False)

# Visible safety signal for every authenticated user. A stale runtime should normally have been
# auto-restored during preflight; true divergence is intentionally surfaced instead of hidden.
sync_blocked=SYNC_PREFLIGHT_STATUS.get('status')=='conflict'
sync_degraded=SYNC_PREFLIGHT_STATUS.get('status')=='remote_error'
is_owner_session=normalized_email(user.get('email'))==normalized_email(secret_value('app','bootstrap_admin_email'))
if SYNC_PREFLIGHT_STATUS.get('status')=='conflict':
    st.error("⚠️ Protección de datos activa: esta instancia detectó una divergencia real con Supabase. Las escrituras quedan bloqueadas hasta que Developer/Owner revise la sincronización.")
elif sync_degraded:
    st.warning("⚠️ Supabase no respondió durante la comprobación inicial. Puedes consultar y preparar la captura normalmente; al pulsar Guardar, la aplicación volverá a validar Supabase en tiempo real y solo aceptará la escritura si el respaldo durable está disponible.")
elif SYNC_PREFLIGHT_STATUS.get('status')=='restored_remote':
    st.toast("Base actualizada automáticamente desde el último respaldo válido de Supabase.",icon="✅")

workflow=inventory_workflow_state()
allowed_inventory_page='Cierre'

with st.sidebar:
    st.image(LOGO_PATH, width=185)
    st.markdown("---")
    st.markdown(f"**{user['name']}**")
    st.caption(f"{ROLE_LABELS.get(user['role'],user['role'])} · {user['email']}")
    st.caption("**Flujo de inventario:** " + _workflow_status_text(workflow))
    if sync_blocked and is_owner_session:
        pages=['Dashboard','Administración']
        st.warning("Modo protegido por conflicto real: Dashboard queda en consulta y Administración permite diagnóstico.")
    elif sync_blocked and user['role'] in ('MANAGER','GENERAL_MANAGER','ADMIN'):
        pages=['Dashboard','Reporte PDF']
        st.warning("Modo consulta por conflicto real: no se permiten escrituras hasta revisión del Developer/Owner.")
    elif sync_blocked:
        pages=[]
        st.warning("Modo protegido por conflicto de datos. Contacta al Manager/Developer.")
    elif user['role'] in ('MANAGER','GENERAL_MANAGER','ADMIN'):
        pages=['Dashboard',allowed_inventory_page,'Inventario semanal','Abastecimiento','POS / Ventas','Recibir pedido','Trasladar productos','Reporte PDF']
        if sync_degraded: st.warning("Conexión Supabase por revalidar. Puedes diligenciar datos; Guardar hará una validación remota obligatoria antes de aceptar la operación.")
    else:
        pages=[allowed_inventory_page,'Inventario semanal','Recibir pedido','Trasladar productos']
        if sync_degraded: st.warning("Conexión Supabase por revalidar. Puedes diligenciar datos; Guardar validará el respaldo antes de aceptar la operación.")
    # MANAGER y MANAGER GENERAL pueden entrar a Administración; las acciones críticas
    # continúan protegidas dentro de la página para ADMIN/Developer Owner.
    if user['role'] in ('MANAGER','GENERAL_MANAGER','ADMIN') and 'Administración' not in pages:
        pages += ['Administración']
    icons={'Dashboard':'▦','Cierre':'↓','Inventario semanal':'📋','Abastecimiento':'🛒','POS / Ventas':'▤','Recibir pedido':'📦','Trasladar productos':'↔','Reporte PDF':'▥','Administración':'⚙'}
    display=[f"{icons.get(p,'•')}  {p}" for p in pages]
    if display:
        selected=st.radio("Navegación",display,label_visibility="collapsed")
        page=pages[display.index(selected)]
    else:
        page=None
    st.markdown("---")
    if st.button("Cerrar sesión",width="stretch"): st.logout()

inventory_flash=st.session_state.pop('_inventory_flash',None)
if inventory_flash:
    if isinstance(inventory_flash,dict):
        level=inventory_flash.get('level','success');msg=inventory_flash.get('message','')
        (st.warning if level=='warning' else st.error if level=='error' else st.success)(msg)
    else:
        st.success(inventory_flash)
if page is None:
    page_header("Sistema en modo protegido","No se aceptan nuevas capturas hasta confirmar la conexión durable con Supabase.")
    st.info("Tus datos existentes no se borraron. Actualiza la página en unos momentos o contacta al Manager/Developer.")
    st.stop()

# --------------------------- pages ---------------------------
if page=='Cierre':
    page_header("Cierre diario", "Conteo físico diario. No requiere Apertura: cada cierre se compara con el cierre anterior, los movimientos del periodo y las ventas POS.")
    wf=inventory_workflow_state(); prog=daily_close_progress(); cycle='DAILY'
    if prog.get('active'):
        d=date.fromisoformat(str(prog['operation_date']))
        st.info(f"Cierre en progreso para {d.strftime('%d/%m/%Y')} · {prog['closing_count']}/{prog['required_count']} productos. Debes completar este mismo cierre antes de iniciar otro.")
        st.date_input("Fecha operativa del cierre",value=d,disabled=True,key='closing_only_date_active')
    else:
        d=st.date_input("Fecha operativa que estás cerrando",value=local_today(),max_value=local_today(),key='closing_only_date_new',help="Selecciona el día operativo al que corresponde el conteo. La hora real de captura se guarda aparte para auditoría, por lo que un cierre después de medianoche puede registrarse con la fecha operativa del día anterior.")
        st.info("No existe un cierre parcial pendiente. Puedes iniciar el cierre cuando corresponda, sin importar la hora. El sistema usará el cierre físico anterior como base de comparación.")
    st.caption("Inventario diario: todas las cervezas + licores principales. El inventario semanal independiente continúa contando todos los productos activos.")
    scope=st.radio("Registrar en esta captura",['Todo el inventario','Solo cervezas','Solo licores'],horizontal=True,key=f'closeonly_scope_{d}')
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id'];wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']
    ps=inventory_products('DAILY');all_ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]
    if scope=='Solo cervezas':ps=[p for p in ps if p['category']=='Cerveza']
    elif scope=='Solo licores':ps=[p for p in ps if p['category']=='Licor']

    # Stable baseline for this close cycle. If the cycle has not started yet, preview the
    # latest valid prior close; when the first capture is saved the exact baseline boundary
    # is frozen inside the immutable close marker.
    if prog.get('active'):
        baseline_id=int(prog.get('baseline_id') or 0);cycle_id=prog.get('cycle_id')
    else:
        base=_latest_daily_closing_boundary(d);baseline_id=int(base['id']) if base else 0;cycle_id=None
    if baseline_id:
        bmeta=one("SELECT session_date,created_at FROM inventory_sessions WHERE id=?",(baseline_id,))
        st.success(f"Base física: último cierre disponible · fecha operativa {bmeta['session_date']} · registrado {format_local_datetime(bmeta['created_at']) if bmeta else '—'}.")
    else:
        st.warning("No existe un cierre anterior comparable. Este conteo se guardará como cierre base; la comparación física comenzará con el siguiente cierre.")

    counts=[]
    for cat in ['Cerveza','Licor']:
        group=[p for p in ps if p['category']==cat]
        if group:st.subheader(cat)
        for p in group:
            prev=_baseline_count_before_id(p['id'],bar,baseline_id) if baseline_id else None
            # If this product was already captured in the current partial close, use its latest
            # value as the default so a deliberate recount is explicit and append-only.
            current=None
            if cycle_id:
                needle=f"%{CLOSE_ONLY_PREFIX}cycle={cycle_id}|%"
                current=one("""SELECT ic.qty_base,ic.qty_bottle_equiv,s.created_at,u.name employee
                               FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
                               LEFT JOIN users u ON u.id=s.user_id
                               WHERE s.notes LIKE ? AND ic.product_id=? AND ic.location_id=?
                               ORDER BY s.id DESC,ic.id DESC LIMIT 1""",(needle,p['id'],bar))
            source=current or prev
            default=float(source['qty_base']) if source is not None else 0.0
            default_bottles=float(source['qty_bottle_equiv']) if source is not None and source['qty_bottle_equiv'] is not None else None
            with st.expander(product_label(p),expanded=True):
                if prev is not None:
                    pv,pbasis=_count_value_for_reconciliation(p,prev)
                    st.info(f"📌 CIERRE ANTERIOR · {_count_text(p,float(prev['qty_base'] or 0),float(prev['qty_bottle_equiv']) if prev['qty_bottle_equiv'] is not None else None)} · fecha {prev['session_date']} · {prev['employee'] or 'Usuario'} · {format_local_time(prev['created_at'])}")
                else:
                    pv,pbasis=(None,'unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle'))
                    st.caption("Primer cierre comparable para este producto: quedará como base física para el próximo periodo.")
                if current is not None:
                    st.caption(f"Ya capturado en este cierre por {current['employee'] or 'Usuario'} a las {format_local_time(current['created_at'])}. Puedes recontarlo; el registro anterior no se borra y queda en auditoría.")
                res=bottle_count_input(p,f"clonly_{d}_{p['id']}",default,default_bottles);val=res['base']
                if prev is not None:
                    close_value=float(res['bottles'] or 0) if pbasis=='bottle' else float(val or 0)
                    # Preview uses the operational date window. Exact immutable baseline is frozen on save.
                    fake_cur={'session_date':d.isoformat(),'created_at':now_iso()}
                    ent=_movement_total_window_in_basis(prev,fake_cur,p,bar,('TRANSFER','SUPPLIER'),'in',pbasis)
                    aj=_movement_total_window_in_basis(prev,fake_cur,p,bar,('PRUEBA','DESPERDICIO','CORTESIA','ROTURA'),'out',pbasis)
                    rc=reconciliation_values(pv,close_value,ent,aj)
                    st.caption(f"Salida física estimada: **{basis_qty_text(p,rc['physical'],pbasis)}** · Ajustes: **{basis_qty_text(p,rc['adjustments'],pbasis)}** · Venta por conteo estimada: **{basis_qty_text(p,rc['count_sale'],pbasis)}**")
                    if rc['stock_gain']>0:st.warning(f"El conteo actual supera el cierre anterior + entradas por {basis_qty_text(p,rc['stock_gain'],pbasis)}. Revisa si falta registrar una entrada o si el conteo es correcto.")
                counts.append({'pid':p['id'],'lid':bar,'qty':val,'bottle_equiv':res['bottles'],'name':p['name'],'category':p['category']})

    st.info(f"Productos en esta captura: {len(ps)} · Cierre diario · {scope}")
    st.divider();pending=[]
    st.subheader("Movimientos pendientes del periodo")
    st.caption("Registra aquí solo movimientos que todavía no hayan sido ingresados. Se guardarán atómicamente junto con este cierre y quedarán incluidos en la comparación entre cierres.")
    if st.toggle("¿Se recibieron productos de proveedor que aún no han sido registrados?",key='clonly_sup_toggle'):
        n=int(st.number_input("Número de productos recibidos",1,30,1,key='clonly_sup_n'));supplier=st.text_input("Proveedor (opcional)",key='clonly_sup_name');ref=st.text_input("Factura / referencia (opcional)",key='clonly_sup_ref');mp={product_label(p):p for p in all_ps}
        for i in range(n):
            nm=st.selectbox(f"Producto recibido {i+1}",list(mp),key=f'clonly_sup_p{i}');p=mp[nm];mv=movement_qty_input(p,f'clonly_sup_q{i}')
            if mv['base']>0 or (mv['bottles'] or 0)>0:pending.append(('SUPPLIER',p['id'],mv['base'],mv['bottles'],None,wh,supplier,ref,''))
    if st.toggle("¿Se trasladaron productos de bodega al bar que aún no han sido registrados?",key='clonly_tr_toggle'):
        n=int(st.number_input("Número de productos trasladados",1,30,1,key='clonly_tr_n'));mp={product_label(p):p for p in all_ps}
        for i in range(n):
            nm=st.selectbox(f"Producto trasladado {i+1}",list(mp),key=f'clonly_tr_p{i}');p=mp[nm];mv=movement_qty_input(p,f'clonly_tr_q{i}')
            if mv['base']>0 or (mv['bottles'] or 0)>0:pending.append(('TRANSFER',p['id'],mv['base'],mv['bottles'],wh,bar,None,None,''))
    if st.toggle("¿Hubo pruebas, desperdicios, cortesías o roturas que aún no estén registradas?",key='clonly_adj_toggle'):
        n=int(st.number_input("Número de ajustes",1,30,1,key='clonly_adj_n'));mp={product_label(p):p for p in all_ps}
        for i in range(n):
            c1,c2=st.columns([1,2]);typ=c1.selectbox(f"Tipo {i+1}",['Prueba','Desperdicio','Cortesía','Rotura / botella quebrada'],key=f'clonly_adj_t{i}');nm=c2.selectbox(f"Producto {i+1}",list(mp),key=f'clonly_adj_p{i}');p=mp[nm]
            mv=movement_qty_input(p,f'clonly_adj_q{i}');obs=st.text_input(f"Observación {i+1} (opcional)",key=f'clonly_adj_o{i}');typdb={'Prueba':'PRUEBA','Desperdicio':'DESPERDICIO','Cortesía':'CORTESIA','Rotura / botella quebrada':'ROTURA'}[typ]
            if mv['base']>0 or (mv['bottles'] or 0)>0:pending.append((typdb,p['id'],mv['base'],mv['bottles'],bar,None,None,None,obs))
    notes=st.text_area("Observaciones generales (opcional)",key=f'clonly_notes_{d}')
    if st.button("Guardar cierre",type="primary",width="stretch"):
        valid,msg=_validate_inventory_save('CLOSING',d,'DAILY')
        if not valid:st.error(msg)
        else:
            result=save_daily_closing_capture(counts,d,notes,pending)
            if not result.get('ok'):st.error(result.get('error','No fue posible guardar el cierre.'))
            else:
                newp=daily_close_progress()
                if result.get('duplicate'):
                    detail=f"La captura ya había sido recibida y **no se creó un duplicado**."
                elif newp.get('active'):
                    detail=f"Cierre diario **parcial** · {newp['closing_count']}/{newp['required_count']} productos. Puedes continuar más tarde o desde otro usuario."
                else:
                    detail="Cierre diario **completo**. El próximo cierre podrá iniciarse cuando corresponda; no existe requisito de Apertura ni restricción por hora o día."
                if result.get('saved'):
                    detail += ("  \nRespaldo automático: **✅ Supabase actualizado**." if result.get('backup_ok') else f"  \n⚠️ El cierre quedó guardado en SQLite, pero el backup automático reportó: {result.get('backup_message','pendiente')}")
                flash_msg=operation_confirmation(('Su cierre fue exitoso y respaldado' if result.get('backup_ok',True) else 'Cierre registrado; respaldo remoto pendiente'),d,detail,result.get('created_at'))
                st.session_state['_inventory_flash']={'level':('success' if result.get('backup_ok',True) else 'warning'),'message':flash_msg};st.rerun()

elif page=='Inventario semanal':
    page_header("Inventario semanal", "Conteo físico independiente de todos los productos activos. No abre ni cierra el turno diario y no genera diferencias contra POS.")
    st.caption("Úsalo cuando el equipo tenga disponibilidad. Puede iniciarse cualquier día, guardarse por partes y continuarse por otros usuarios hasta completar todos los productos.")
    st.info("Este conteo alimenta el stock físico y el abastecimiento. El cierre diario continúa limitado a cervezas + licores principales.")
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    active_weekly=weekly_active_session()
    recent_weekly=weekly_recent_sessions(6)

    if not active_weekly:
        if recent_weekly:
            last=recent_weekly[0]
            status_txt='Completo' if last['status']=='COMPLETED' else 'En progreso'
            st.caption(f"Último inventario semanal: {last['inventory_date']} · {status_txt} · {int(last['counted_count'] or 0)}/{int(last['required_count'] or 0)} productos.")
        c1,c2=st.columns([1,2])
        weekly_date=c1.date_input("Fecha del inventario semanal",value=local_today(),disabled=True,key='weekly_start_date')
        weekly_start_note=c2.text_input("Observación de inicio (opcional)",key='weekly_start_note')
        if st.button("Iniciar inventario semanal",type="primary",width="stretch",key='weekly_start_btn'):
            result=start_weekly_inventory(weekly_date,weekly_start_note)
            if not result.get('ok'):
                st.error(result.get('error','No fue posible iniciar el inventario semanal.'))
            else:
                if result.get('existing'):
                    st.info("Ya existía un inventario semanal en progreso. Se abrirá para continuar.")
                elif result.get('backup_ok'):
                    st.success("Inventario semanal iniciado y respaldado en Supabase.")
                else:
                    st.warning("Inventario semanal iniciado en SQLite; el respaldo remoto quedó pendiente: "+str(result.get('backup_message','')))
                st.rerun()
        if recent_weekly:
            st.subheader("Historial semanal reciente")
            hist=[]
            for r in recent_weekly:
                hist.append({
                    'Fecha':r['inventory_date'],
                    'Estado':'✅ Completo' if r['status']=='COMPLETED' else '🟡 En progreso',
                    'Progreso':f"{int(r['counted_count'] or 0)}/{int(r['required_count'] or 0)}",
                    'Iniciado por':r['started_by'] or 'Usuario',
                    'Inicio':format_local_datetime(r['started_at'],'%d/%m/%Y %I:%M %p') if r['started_at'] else '—',
                    'Finalizado por':r['completed_by'] or '—',
                    'Fin':format_local_datetime(r['completed_at'],'%d/%m/%Y %I:%M %p') if r['completed_at'] else '—',
                })
            st.dataframe(pd.DataFrame(hist),width='stretch',hide_index=True)
        st.stop()

    weekly_id=int(active_weekly['id'])
    weekly_prog=weekly_inventory_progress(weekly_id)
    required_products=weekly_session_products(weekly_id)
    st.success(
        f"Inventario semanal en progreso · fecha física {active_weekly['inventory_date']} · "
        f"{weekly_prog['counted_count']}/{weekly_prog['required_count']} productos · "
        f"iniciado por {active_weekly['started_by'] or 'Usuario'} a las {format_local_time(active_weekly['started_at'])}."
    )
    m1,m2,m3=st.columns(3)
    m1.metric("Productos requeridos",weekly_prog['required_count'])
    m2.metric("Registrados",weekly_prog['counted_count'])
    m3.metric("Pendientes",max(weekly_prog['required_count']-weekly_prog['counted_count'],0))
    st.progress((weekly_prog['counted_count']/weekly_prog['required_count']) if weekly_prog['required_count'] else 0.0)

    scope=st.radio("Productos a registrar ahora",['Todo el inventario','Solo cervezas','Solo licores'],horizontal=True,key=f'weekly_scope_{weekly_id}')
    pending_only=st.checkbox("Mostrar solo productos pendientes",value=True,key=f'weekly_pending_only_{weekly_id}',help="Desmárcalo si necesitas volver a contar un producto antes de finalizar.")
    ps=list(required_products)
    if scope=='Solo cervezas':ps=[p for p in ps if p['category']=='Cerveza']
    elif scope=='Solo licores':ps=[p for p in ps if p['category']=='Licor']
    if pending_only:ps=[p for p in ps if int(p['id']) in weekly_prog['pending_ids']]

    counts=[]
    if not ps:
        st.info("No hay productos pendientes en esta selección. Puedes cambiar la categoría o desmarcar «Mostrar solo productos pendientes» para recontar.")
    for cat in ['Cerveza','Licor']:
        group=[p for p in ps if p['category']==cat]
        if group:st.subheader(cat)
        for p in group:
            current=weekly_latest_count(weekly_id,p['id'],bar)
            prior=weekly_last_completed_count(p['id'],bar,active_weekly['inventory_date']) if current is None else None
            default_base=0.0;default_bottles=None
            with st.expander(product_label(p),expanded=True):
                if current is not None:
                    default_base=float(current['qty_base'] or 0)
                    default_bottles=float(current['qty_bottle_equiv']) if current['qty_bottle_equiv'] is not None else None
                    if p['category']=='Licor' and not p['bottle_ml'] and default_bottles is not None:
                        st.info(f"Último conteo de este semanal: {default_bottles:.2f} bot · {current['employee'] or 'Usuario'} · {format_local_time(current['created_at'])}. Puedes recontarlo antes de finalizar.")
                    else:
                        st.info(f"Último conteo de este semanal: {qty_fmt(p,default_base)} · {current['employee'] or 'Usuario'} · {format_local_time(current['created_at'])}. Puedes recontarlo antes de finalizar.")
                elif prior is not None:
                    default_base=float(prior['qty_base'] or 0)
                    default_bottles=float(prior['qty_bottle_equiv']) if prior['qty_bottle_equiv'] is not None else None
                    if p['category']=='Licor' and not p['bottle_ml'] and default_bottles is not None:
                        st.caption(f"Referencia del último semanal ({prior['inventory_date']}): {default_bottles:.2f} bot · solo guía, no bloquea el conteo.")
                    else:
                        st.caption(f"Referencia del último semanal ({prior['inventory_date']}): {qty_fmt(p,default_base)} · solo guía, no bloquea el conteo.")
                else:
                    # If this product has never been in a completed weekly snapshot, show the latest
                    # operational stock as a guide. It is not interpreted as a weekly count until saved.
                    ref,ref_basis=current_stock_basis(p,bar)
                    if ref_basis=='bottle':
                        default_bottles=ref;default_base=0.0
                        st.caption(f"Referencia física disponible: {basis_qty_text(p,ref,ref_basis)} · solo guía.")
                    else:
                        default_base=ref
                        if p['category']=='Licor' and p['bottle_ml']:
                            default_bottles=ref/bottle_oz(p) if bottle_oz(p) else None
                        st.caption(f"Referencia física disponible: {basis_qty_text(p,ref,ref_basis)} · solo guía.")
                res=bottle_count_input(p,f"wk_{weekly_id}_{p['id']}",default_base,default_bottles)
                obs=st.text_input("Observación (opcional)",key=f"wkobs_{weekly_id}_{p['id']}")
                counts.append({'pid':p['id'],'lid':bar,'qty':res['base'],'bottle_equiv':res['bottles'],'obs':obs,'name':p['name'],'category':p['category'],
                               'expected_count_id':(int(current['id']) if current is not None else None)})

    capture_note=st.text_input("Nota de esta captura (opcional)",key=f'weekly_capture_note_{weekly_id}')
    if counts and st.button("Guardar avance semanal",type="primary",width="stretch",key=f'weekly_save_{weekly_id}'):
        result=save_weekly_inventory_progress(weekly_id,counts,scope,capture_note)
        if not result.get('ok'):
            st.error(result.get('error','No fue posible guardar el avance semanal.'))
        else:
            new_prog=weekly_inventory_progress(weekly_id)
            if result.get('duplicate'):
                detail=f"La captura ya había sido recibida; no se creó un duplicado. Progreso {new_prog['counted_count']}/{new_prog['required_count']}."
            else:
                detail=f"Avance semanal guardado · {new_prog['counted_count']}/{new_prog['required_count']} productos."
                detail += ("  \nRespaldo automático: **✅ Supabase actualizado**." if result.get('backup_ok') else f"  \n⚠️ Guardado en SQLite; backup remoto: {result.get('backup_message','pendiente')}")
            st.session_state['_inventory_flash']={
                'level':('success' if result.get('backup_ok',True) else 'warning'),
                'message':operation_confirmation(('Avance semanal guardado y respaldado' if result.get('backup_ok',True) else 'Avance semanal guardado; respaldo pendiente'),date.fromisoformat(active_weekly['inventory_date']),detail,result.get('created_at'))
            }
            st.rerun()

    # Refresh after any UI interactions; finalization is intentionally separate from data capture.
    weekly_prog=weekly_inventory_progress(weekly_id)
    st.divider()
    if weekly_prog['complete']:
        st.success("Todos los productos del inventario semanal ya tienen conteo. Puedes revisarlos/recontarlos o finalizar el inventario.")
        final_note=st.text_area("Observación final (opcional)",key=f'weekly_final_note_{weekly_id}')
        if st.button("Finalizar inventario semanal",type="primary",width="stretch",key=f'weekly_complete_{weekly_id}'):
            result=complete_weekly_inventory(weekly_id,final_note)
            if not result.get('ok'):
                st.error(result.get('error','No fue posible finalizar el inventario semanal.'))
            else:
                detail=f"Inventario semanal completo · {weekly_prog['counted_count']}/{weekly_prog['required_count']} productos. Este conteo queda como fotografía física independiente y no genera diferencias contra POS."
                detail += ("  \nRespaldo automático: **✅ Supabase actualizado**." if result.get('backup_ok',True) else f"  \n⚠️ Finalizado en SQLite; backup remoto: {result.get('backup_message','pendiente')}")
                st.session_state['_inventory_flash']={
                    'level':('success' if result.get('backup_ok',True) else 'warning'),
                    'message':operation_confirmation(('Inventario semanal finalizado y respaldado' if result.get('backup_ok',True) else 'Inventario semanal finalizado; respaldo pendiente'),date.fromisoformat(active_weekly['inventory_date']),detail,result.get('created_at'))
                }
                st.rerun()
    else:
        st.caption(f"Para finalizar faltan {weekly_prog['required_count']-weekly_prog['counted_count']} productos. Puedes salir de la aplicación y continuar más tarde; cada avance ya guardado permanece en SQLite y Supabase.")

    if recent_weekly:
        st.subheader("Inventarios semanales recientes")
        hist=[]
        for r in recent_weekly:
            hist.append({'Fecha':r['inventory_date'],'Estado':'✅ Completo' if r['status']=='COMPLETED' else '🟡 En progreso','Progreso':f"{int(r['counted_count'] or 0)}/{int(r['required_count'] or 0)}",'Iniciado por':r['started_by'] or 'Usuario','Finalizado por':r['completed_by'] or '—'})
        st.dataframe(pd.DataFrame(hist),width='stretch',hide_index=True)

elif page=='Recibir pedido':
    page_header("Recibir pedido", "Registra entradas de proveedor en bodega o bar.")
    st.caption("Opción adicional: úsala si puedes registrar el pedido cuando llega. Si no, podrá ingresarse más tarde desde el cierre diario.")
    d=st.date_input("Fecha de recepción",value=local_today()); supplier=st.text_input("Proveedor"); ref=st.text_input("Factura / referencia (opcional)")
    wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    dest_name=st.selectbox("Destino",['Bodega','Bar'],index=0,disabled=user['role']=='STAFF')
    dest=wh if dest_name=='Bodega' else bar
    ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; n=int(st.number_input("Número de productos recibidos",1,50,1)); mp={product_label(p):p for p in ps}; rows=[]
    for i in range(n):
        nm=st.selectbox(f"Producto {i+1}",list(mp),key=f'rp{i}'); p=mp[nm]; mv=movement_qty_input(p,f'rq{i}')
        obs=st.text_input(f"Observación {i+1} (opcional)",key=f'ro{i}')
        if mv['base']>0 or (mv['bottles'] or 0)>0: rows.append((p['id'],mv['base'],mv['bottles'],obs))
    if st.button("Confirmar recepción",type="primary",width="stretch"):
        if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
        else:
            entries=[{'date':d.isoformat(),'type':'SUPPLIER','pid':pid,'qty':qty,'from_id':None,'to_id':dest,'supplier':supplier,'reference':ref,'obs':obs,'bottle_equiv':beq} for pid,qty,beq,obs in rows]
            result=save_movements_batch(entries)
            if not result.get('ok'):
                st.error(result.get('error','No fue posible registrar la recepción.'))
            else:
                detail=f"{len(rows)} producto(s) · Destino: **{dest_name}**" + (" · Backup durable ✅" if result.get('backup_ok') else f" · ⚠️ Backup pendiente: {result.get('backup_message')}")
                st.success(operation_confirmation('Su recepción de productos fue registrada correctamente',d,detail,result.get('created_at')))

elif page=='Trasladar productos':
    page_header("Trasladar productos", "Registra movimientos de inventario entre bodega y bar.")
    st.caption("Opción adicional para registrar un traslado en el momento. Si no hay tiempo, puede registrarse después como movimiento pendiente.")
    d=st.date_input("Fecha del traslado",value=local_today()); wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; n=int(st.number_input("Número de productos trasladados",1,50,1)); mp={product_label(p):p for p in ps}; rows=[]
    for i in range(n):
        nm=st.selectbox(f"Producto {i+1}",list(mp),key=f'tp{i}'); p=mp[nm]; mv=movement_qty_input(p,f'tq{i}')
        if mv['base']>0 or (mv['bottles'] or 0)>0: rows.append((p['id'],mv['base'],mv['bottles']))
    if st.button("Confirmar traslado Bodega → Bar",type="primary",width="stretch"):
        if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
        else:
            entries=[{'date':d.isoformat(),'type':'TRANSFER','pid':pid,'qty':qty,'from_id':wh,'to_id':bar,'supplier':None,'reference':None,'obs':'','bottle_equiv':beq} for pid,qty,beq in rows]
            result=save_movements_batch(entries)
            if not result.get('ok'):
                st.error(result.get('error','No fue posible registrar el traslado.'))
            else:
                detail=f"{len(rows)} producto(s) trasladado(s)" + (" · Backup durable ✅" if result.get('backup_ok') else f" · ⚠️ Backup pendiente: {result.get('backup_message')}")
                st.success(operation_confirmation('Su traslado Bodega → Bar fue registrado correctamente',d,detail,result.get('created_at')))

elif page=='POS / Ventas':
    page_header("POS / Ventas", "Registra ventas de cócteles, shots, cervezas y botellas para calcular el consumo teórico.")
    st.caption("Ingresa los totales vendidos del POS por fecha. Shots y cervezas quedan registrados directamente contra el producto correspondiente.")
    d=st.date_input("Fecha de ventas",value=local_today(),key='pos_date')
    tab_cocktail,tab_shot,tab_beer,tab_bottle=st.tabs(['🍹 Cócteles','🥃 Shots','🍺 Cervezas','🍾 Botellas de licor'])

    with tab_cocktail:
        items=q("SELECT * FROM cocktails WHERE active=1 ORDER BY name")
        if not items:
            st.info("No hay cócteles activos. Puedes crearlos en Administración → Cócteles / Recetas.")
        else:
            mp={r['name']:r['id'] for r in items}
            n=int(st.number_input("Número de cócteles con ventas",1,30,1,key='pos_c_n'))
            rows=[]
            for i in range(n):
                c1,c2=st.columns([2,1])
                nm=c1.selectbox(f"Cóctel {i+1}",list(mp),key=f'pos_c_name_{i}')
                qty=float(c2.number_input(f"Cantidad {i+1}",min_value=0,step=1,value=0,key=f'pos_c_qty_{i}'))
                if qty>0: rows.append((mp[nm],qty))
            obs=st.text_input("Observación general (opcional)",key='pos_c_obs')
            if st.button("Guardar ventas de cócteles",type='primary',width='stretch',key='save_pos_cocktails'):
                if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    payload=[{'cocktail_id':cid,'product_id':None,'sale_type':'Cóctel','quantity':qty,'oz_per_unit':None} for cid,qty in rows]
                    result=save_pos_group(d,'COCKTAIL',payload,obs)
                    if not result.get('ok'): st.error(result.get('error','No fue posible guardar POS de cócteles.'))
                    else: st.success(operation_confirmation('Sus ventas POS de cócteles fueron guardadas correctamente',d,f"{len(rows)} registro(s) · POS de cócteles confirmado · " + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

        if st.button('Confirmar 0 ventas de cócteles',key='pos_c_zero',width='stretch'):
            result=save_pos_group(d,'COCKTAIL',[],'Confirmado sin ventas')
            if not result.get('ok'): st.error(result.get('error','No fue posible confirmar POS.'))
            else: st.success(operation_confirmation('Su POS de cócteles fue confirmado correctamente',d,'Ventas registradas: **0** · ' + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

    with tab_shot:
        liquors=products('Licor')
        if not liquors:
            st.info("No hay licores activos.")
        else:
            mp={product_label(r):r for r in liquors}
            n=int(st.number_input("Número de licores vendidos como shot",1,30,1,key='pos_s_n'))
            rows=[]
            for i in range(n):
                c1,c2,c3=st.columns([2,1,1])
                nm=c1.selectbox(f"Licor {i+1}",list(mp),key=f'pos_s_name_{i}'); prod=mp[nm]
                qty=float(c2.number_input(f"Shots {i+1}",min_value=0,step=1,value=0,key=f'pos_s_qty_{i}'))
                oz=float(c3.number_input(f"Oz/shot {i+1}",min_value=.25,step=.25,value=1.0,key=f'pos_s_oz_{i}'))
                if qty>0: rows.append((prod['id'],qty,oz))
            obs=st.text_input("Observación general (opcional)",key='pos_s_obs')
            if st.button("Guardar ventas de shots",type='primary',width='stretch',key='save_pos_shots'):
                if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    payload=[{'cocktail_id':None,'product_id':pid,'sale_type':'Shot','quantity':qty,'oz_per_unit':oz} for pid,qty,oz in rows]
                    result=save_pos_group(d,'SHOT',payload,obs)
                    if not result.get('ok'): st.error(result.get('error','No fue posible guardar POS de shots.'))
                    else: st.success(operation_confirmation('Sus ventas POS de shots fueron guardadas correctamente',d,f"{len(rows)} registro(s) · POS de shots confirmado · " + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

        if st.button('Confirmar 0 ventas de shots',key='pos_s_zero',width='stretch'):
            result=save_pos_group(d,'SHOT',[],'Confirmado sin ventas')
            if not result.get('ok'): st.error(result.get('error','No fue posible confirmar POS.'))
            else: st.success(operation_confirmation('Su POS de shots fue confirmado correctamente',d,'Ventas registradas: **0** · ' + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

    with tab_beer:
        beers=products('Cerveza')
        if not beers:
            st.info("No hay cervezas activas.")
        else:
            st.caption("Escribe únicamente las unidades vendidas. Las cervezas en cero no generan registros.")
            beer_rows=[]
            cols=st.columns(2)
            for i,p in enumerate(beers):
                with cols[i%2]:
                    qty=float(st.number_input(product_label(p),min_value=0,step=1,value=0,key=f'pos_b_qty_{p["id"]}'))
                    if qty>0: beer_rows.append((p['id'],qty))
            obs=st.text_input("Observación general (opcional)",key='pos_b_obs')
            if st.button("Guardar ventas de cervezas",type='primary',width='stretch',key='save_pos_beers'):
                if not beer_rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    payload=[{'cocktail_id':None,'product_id':pid,'sale_type':'Cerveza','quantity':qty,'oz_per_unit':None} for pid,qty in beer_rows]
                    result=save_pos_group(d,'BEER',payload,obs)
                    if not result.get('ok'): st.error(result.get('error','No fue posible guardar POS de cervezas.'))
                    else: st.success(operation_confirmation('Sus ventas POS de cervezas fueron guardadas correctamente',d,f"{len(beer_rows)} producto(s) · POS de cervezas confirmado · " + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

        if st.button('Confirmar 0 ventas de cervezas',key='pos_b_zero',width='stretch'):
            result=save_pos_group(d,'BEER',[],'Confirmado sin ventas')
            if not result.get('ok'): st.error(result.get('error','No fue posible confirmar POS.'))
            else: st.success(operation_confirmation('Su POS de cervezas fue confirmado correctamente',d,'Ventas registradas: **0** · ' + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

    with tab_bottle:
        liquors=products('Licor')
        if not liquors:
            st.info("No hay licores activos.")
        else:
            mp={product_label(r):r for r in liquors}
            n=int(st.number_input("Número de licores vendidos por botella",1,20,1,key='pos_l_n'))
            rows=[]
            for i in range(n):
                c1,c2=st.columns([2,1])
                nm=c1.selectbox(f"Licor {i+1}",list(mp),key=f'pos_l_name_{i}'); prod=mp[nm]
                qty=float(c2.number_input(f"Botellas {i+1}",min_value=0,step=1,value=0,key=f'pos_l_qty_{i}'))
                if qty>0: rows.append((prod['id'],qty))
            obs=st.text_input("Observación general (opcional)",key='pos_l_obs')
            if st.button("Guardar ventas por botella",type='primary',width='stretch',key='save_pos_bottles'):
                if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    payload=[{'cocktail_id':None,'product_id':pid,'sale_type':'Botella de licor','quantity':qty,'oz_per_unit':None} for pid,qty in rows]
                    result=save_pos_group(d,'LIQUOR_BOTTLE',payload,obs)
                    if not result.get('ok'): st.error(result.get('error','No fue posible guardar POS de botellas.'))
                    else: st.success(operation_confirmation('Sus ventas POS de botellas de licor fueron guardadas correctamente',d,f"{len(rows)} registro(s) · POS de botellas confirmado · " + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

        if st.button('Confirmar 0 ventas de botellas de licor',key='pos_l_zero',width='stretch'):
            result=save_pos_group(d,'LIQUOR_BOTTLE',[],'Confirmado sin ventas')
            if not result.get('ok'): st.error(result.get('error','No fue posible confirmar POS.'))
            else: st.success(operation_confirmation('Su POS de botellas de licor fue confirmado correctamente',d,'Ventas registradas: **0** · ' + ('Backup durable ✅' if result.get('backup_ok') else '⚠️ Backup pendiente'),result.get('created_at')))

elif page=='Dashboard':
    page_header("Dashboard Operacional", "Inventario, ventas, diferencias, alertas y actividad en una sola vista.")

    # Un botón explícito evita que una sesión gerencial abierta quede mostrando datos antiguos
    # después de que otro usuario registre información desde otro dispositivo.
    top_refresh,top_note=st.columns([1,4])
    if top_refresh.button("🔄 Actualizar datos",width='stretch',key='dash_refresh'):
        st.rerun()
    top_note.caption(f"Última actualización de esta vista: {local_now().strftime('%I:%M:%S %p')} · Ontario")

    f1,f2,f3=st.columns([1.15,1.45,1.3])
    period=f1.selectbox("Periodo",['Hoy','7 días','Semana','Mes','Personalizado'],index=0,key='dash_period_v4')
    category_view=f2.selectbox("Ver",['General','Licores','Cervezas','Cócteles','Shots'],index=0,key='dash_category_v4')
    status_view=f3.selectbox("Estado",['Todos','Con alerta','Pendientes','OK'],index=0,key='dash_status_v4')
    if period=='Hoy':
        d1=d2=local_today()
    elif period=='7 días':
        d2=local_today(); d1=d2-timedelta(days=6)
    elif period=='Semana':
        d2=local_today(); d1=d2-timedelta(days=d2.weekday())
    elif period=='Mes':
        d2=local_today(); d1=d2.replace(day=1)
    else:
        a,b=st.columns(2)
        d1=a.date_input("Desde",value=local_today()-timedelta(days=6),key='dash1_v4')
        d2=b.date_input("Hasta",value=local_today(),key='dash2_v4')
    if d2<d1:
        st.error("La fecha final no puede ser anterior a la inicial."); st.stop()

    # El bloque operacional debe respetar el periodo seleccionado. Si el periodo
    # incluye varios días, usamos como referencia el último día que realmente tenga
    # un inventario registrado, en vez de forzar siempre la fecha de hoy.
    latest_inventory_date=_latest_inventory_date_in_period(d1,d2)
    snapshot_date=latest_inventory_date or d2
    # V0.4.8 resolves each product independently within the same inventory cycle.
    # This preserves partial submissions made at different hours by different users.
    period_snapshot,cycle=today_inventory_snapshot(snapshot_date)
    total_required,registered_period,open_done,close_done,inventory_state=_inventory_progress_today(period_snapshot)
    current_alerts=[r for r in period_snapshot if r['_state']=='ALERT']
    current_reviews=[r for r in period_snapshot if r['_state']=='REVIEW']
    last_act=_last_inventory_activity(snapshot_date.isoformat()) if latest_inventory_date else None

    beer_sold=one("SELECT COALESCE(SUM(quantity),0) x FROM pos_sales WHERE sale_type='Cerveza' AND sale_date BETWEEN ? AND ?",(d1.isoformat(),d2.isoformat()))['x']
    cocktails_sold=one("SELECT COALESCE(SUM(quantity),0) x FROM pos_sales WHERE sale_type='Cóctel' AND sale_date BETWEEN ? AND ?",(d1.isoformat(),d2.isoformat()))['x']
    shots_sold=one("SELECT COALESCE(SUM(quantity),0) x FROM pos_sales WHERE sale_type='Shot' AND sale_date BETWEEN ? AND ?",(d1.isoformat(),d2.isoformat()))['x']

    perf=period_inventory_performance(d1,d2)
    perf_complete=[r for r in perf if r['Días completos']>0 and r['Diferencia'] is not None]
    worst=max(perf_complete,key=lambda r:abs(float(r['Diferencia'] or 0)),default=None)
    if not worst:
        current_comp=[r for r in period_snapshot if r['_diff'] is not None]
        worst=max(current_comp,key=lambda r:abs(float(r['_diff'] or 0)),default=None)
        worst_text=(worst['Diferencia'] if worst else '—')
        worst_name=(worst['Producto'] if worst else 'Sin diferencia comparable')
    else:
        unit='bot' if worst['Categoría']=='Cerveza' else 'oz'
        worst_text=f"{float(worst['Diferencia']):+.2f} {unit}"
        worst_name=worst['Producto']

    # KPIs operacionales
    k1,k2,k3,k4,k5,k6=st.columns(6)
    inv_kpi_label='Inventario de hoy' if d1==d2==local_today() else 'Último inventario'
    inv_kpi_delta=((snapshot_date.strftime('%d/%m/%Y')+' · '+('Semanal' if cycle=='WEEKLY' else 'Diario')) if latest_inventory_date else 'Sin registros en el periodo')
    k1.metric(inv_kpi_label,inventory_state,delta=inv_kpi_delta)
    k2.metric("Productos registrados",f"{registered_period} / {total_required}",delta=f"{(registered_period/total_required*100):.0f}%" if total_required else '—')
    k3.metric("Alertas críticas",len(current_alerts),delta=f"{len(current_reviews)} por revisar")
    k4.metric("Mayor diferencia",worst_text,delta=worst_name)
    k5.metric("Cervezas vendidas",f"{float(beer_sold or 0):,.0f}",delta=period)
    k6.metric("Cócteles vendidos",f"{float(cocktails_sold or 0):,.0f}",delta=f"{float(shots_sold or 0):,.0f} shots")

    # Estado de inventario + alertas + actividad
    s1,s2,s3=st.columns([1.05,1.15,1.15])
    with s1:
        st.markdown(f'<div class="ramona-section">📋 Estado de inventario · {snapshot_date.strftime("%d/%m/%Y")}</div>',unsafe_allow_html=True)
        baseline_txt='✅ Disponible' if open_done else '⏳ Sin cierre anterior'
        closing_txt='✅ Registrado' if close_done else '⏳ Pendiente'
        ds_reference=snapshot_date.isoformat()
        beer_pos_ok=pos_group_submitted(ds_reference,'BEER')
        liquor_pos_done=sum(1 for g in ('COCKTAIL','SHOT','LIQUOR_BOTTLE') if pos_group_submitted(ds_reference,g))
        status_rows=[
            {'Área':'Cervezas','Estado':_category_progress(period_snapshot,'Cerveza')},
            {'Área':'Licores principales' if cycle=='DAILY' else 'Licores','Estado':_category_progress(period_snapshot,'Licor')},
            {'Área':'Cierre anterior','Estado':baseline_txt},
            {'Área':'Cierre actual','Estado':closing_txt},
            {'Área':'POS cervezas','Estado':'✅ Confirmado' if beer_pos_ok else '⏳ Pendiente'},
            {'Área':'POS licor','Estado':f"{'✅ Confirmado' if liquor_pos_done==3 else '⏳ Pendiente'} · {liquor_pos_done}/3 secciones"},
        ]
        if last_act:
            status_rows.append({'Área':'Último registro','Estado':f"{last_act['employee']} · {format_local_time(last_act['created_at'])}"})
        st.dataframe(pd.DataFrame(status_rows),width='stretch',hide_index=True)
    with s2:
        st.markdown('<div class="ramona-section">🚨 Alertas prioritarias</div>',unsafe_allow_html=True)
        priority=[r for r in period_snapshot if r['_state'] in ('ALERT','REVIEW')]
        if priority:
            pr=[]
            for r in sorted(priority,key=lambda x:max(abs(float(x['_diff'] or 0)),float(x.get('_stock_gain') or 0),float(x.get('_adjustment_excess') or 0)),reverse=True)[:6]:
                pr.append({'Producto':r['Producto'],'Diferencia':r['Diferencia'],'Incidencia':r.get('Incidencia física','—'),'Estado':r['Alerta']})
            st.dataframe(pd.DataFrame(pr),width='stretch',hide_index=True)
        else:
            st.success("No hay diferencias con alerta entre venta por conteo y POS en el inventario de referencia seleccionado.")
    with s3:
        st.markdown('<div class="ramona-section">🕒 Actividad reciente</div>',unsafe_allow_html=True)
        acts=recent_activity(7)
        if acts: st.dataframe(pd.DataFrame(acts),width='stretch',hide_index=True)
        else: st.info("Todavía no hay actividad registrada.")

    # -------- filtros de vista --------
    if category_view in ('General','Licores','Cervezas'):
        st.markdown(f'<div class="ramona-section">📦 Detalle de inventario · {snapshot_date.strftime("%d/%m/%Y")}</div>',unsafe_allow_html=True)
        physical=period_snapshot
        if category_view=='Licores': physical=[r for r in physical if r['Tipo']=='Licor']
        elif category_view=='Cervezas': physical=[r for r in physical if r['Tipo']=='Cerveza']
        physical=_status_filter(physical,status_view)
        if physical:
            cols=['Producto','Tipo','Cierre anterior','Cierre actual','Entradas','Salida física','Ajustes','Venta por conteo','Ventas POS / recetas','Diferencia','Incidencia física','Alerta','Empleado','Hora']
            display_rows=[]
            for r in physical:
                rr=dict(r); rr['Salida física']=rr.get('Consumo físico','—')
                display_rows.append({c:rr[c] for c in cols})
            st.dataframe(pd.DataFrame(display_rows),width='stretch',hide_index=True)
            st.caption(f"Vista física correspondiente al último inventario registrado dentro del periodo: {snapshot_date.strftime('%d/%m/%Y')}. Salida física = cierre anterior + entradas al bar − cierre actual (nunca se muestra negativa). Venta por conteo = salida física − ajustes autorizados. Diferencia = venta por conteo − POS; puede ser positiva o negativa y genera revisión en ambos sentidos. Si el cierre actual supera cierre anterior + entradas, se marca como aumento de stock no explicado.")
        else:
            st.info("No hay productos que coincidan con los filtros seleccionados.")

        # Rendimiento del periodo solo con días físicamente comparables.
        st.markdown('<div class="ramona-section">📊 Venta por conteo vs POS</div>',unsafe_allow_html=True)
        perf_view=perf
        if category_view=='Licores': perf_view=[r for r in perf if r['Categoría']=='Licor']
        elif category_view=='Cervezas': perf_view=[r for r in perf if r['Categoría']=='Cerveza']
        perf_view=[r for r in perf_view if r['Días completos']>0]
        if status_view!='Todos': perf_view=_status_filter(perf_view,status_view)
        if perf_view:
            perf_show=[]
            for r in perf_view:
                p=r['_p']
                basis=r.get('_basis','unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle'))
                pos_txt=basis_qty_text(p,r['Ventas POS'],basis) if r['Días POS completos']==r['Días completos'] and basis!='bottle' else ('⚠ Falta ml para comparar' if basis=='bottle' else 'Pendiente POS')
                perf_show.append({'Producto':r['Producto'],'Tipo':r['Categoría'],
                                  'Salida física':basis_qty_text(p,r['Consumo físico'],basis),
                                  'Ajustes':basis_qty_text(p,r['Ajustes'],basis),
                                  'Venta por conteo':basis_qty_text(p,r['Venta por conteo'],basis),
                                  'Ventas POS / recetas':pos_txt,
                                  'Diferencia':r['_diff_text'],'Incidencia física':r.get('Incidencia física','—'),'Estado':r['Estado'],'Días físicos':r['Días completos'],'Días POS':r['Días POS completos']})
            st.dataframe(pd.DataFrame(perf_show),width='stretch',hide_index=True)
            st.caption('Interpretación de la diferencia: positiva = el conteo físico indica más ventas/salidas que el POS; negativa = el POS registra más ventas que las explicadas por el conteo. En ambos casos se revisa si supera la tolerancia. Pruebas, desperdicios, cortesías y roturas se descuentan antes de comparar con POS.')
        else:
            st.info("Aún no hay cierres consecutivos comparables en este periodo. La diferencia solo se calcula cuando también está confirmado el POS relevante.")

        if category_view=='Cervezas':
            st.markdown('<div class="ramona-section">🍺 Ventas de cervezas POS</div>',unsafe_allow_html=True)
            bsum=beer_sales_summary(d1,d2)
            if bsum: st.dataframe(pd.DataFrame(bsum),width='stretch',hide_index=True)
            else: st.info("No hay ventas de cerveza registradas en el periodo.")

        # Tendencias: separadas por unidad para no mezclar oz con unidades.
        if category_view in ('General','Licores'):
            st.markdown('<div class="ramona-section">📈 Venta por conteo vs POS · licores</div>',unsafe_allow_html=True)
            lt=daily_trend(d1,d2,'Licor')
            if len(lt): st.line_chart(lt.set_index('Fecha'),width='stretch')
            else: st.info("Sin datos suficientes de licores para graficar.")
        if category_view in ('General','Cervezas'):
            st.markdown('<div class="ramona-section">📈 Venta por conteo vs POS · cervezas</div>',unsafe_allow_html=True)
            bt=daily_trend(d1,d2,'Cerveza')
            if len(bt): st.line_chart(bt.set_index('Fecha'),width='stretch')
            else: st.info("Sin datos suficientes de cerveza para graficar.")

        if category_view=='General':
            st.markdown('<div class="ramona-section">🛒 Abastecimiento rápido</div>',unsafe_allow_html=True)
            bar_id=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh_id=one("SELECT id FROM locations WHERE name='Bodega'")['id']
            safety=float(setting('safety_stock_pct','15'))/100
            days_period=max((d2-d1).days+1,1)
            buy_rows=[]
            for r in perf:
                if r['Días completos']<=0: continue
                p=r['_p']; basis=r.get('_basis','unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle'))
                daily=max(float(r['Consumo real'] or 0),0)/r['Días completos']; target=daily*7*(1+safety)
                sb,sbb=current_stock_basis(p,bar_id); sw,swb=current_stock_basis(p,wh_id)
                if sbb!=basis or swb!=basis: continue
                stock=max(sb+sw,0); need=max(target-stock,0)
                if need<=0: continue
                if p['category']=='Cerveza': action=f"Comprar {math.ceil(need)} unid"
                elif basis=='bottle': action=f"Comprar {math.ceil(need)} bot"
                else:
                    boz=bottle_oz(p); action=(f"Comprar {math.ceil(need/boz)} bot" if boz else '⚠ Falta ml')
                buy_rows.append({'Producto':p['name'],'Necesidad':basis_qty_text(p,need,basis),'Acción sugerida':action})
            if buy_rows:
                st.dataframe(pd.DataFrame(buy_rows[:8]),width='stretch',hide_index=True)
            else:
                st.success("No hay necesidad de compra calculable con los días completos del periodo.")

    elif category_view=='Cócteles':
        st.markdown('<div class="ramona-section">🍹 Cócteles</div>',unsafe_allow_html=True)
        rows=cocktail_sales_summary(d1,d2)
        rows=_status_filter(rows,status_view)
        if rows:
            show=[]
            for r in rows:
                show.append({'Cóctel':r['Cóctel'],'Vendidos':f"{r['Vendidos']:.0f}",
                             'Oz licor / cóctel':f"{r['Oz licor / cóctel']:.2f}" if r['Oz licor / cóctel'] is not None else '—',
                             'Consumo teórico':f"{r['Consumo teórico']:.2f} oz",'Estado':r['Estado']})
            st.dataframe(pd.DataFrame(show),width='stretch',hide_index=True)
            sold_rows=[r for r in rows if r['Vendidos']>0]
            if sold_rows:
                chart=pd.DataFrame({'Cóctel':[r['Cóctel'] for r in sold_rows],'Vendidos':[r['Vendidos'] for r in sold_rows]}).set_index('Cóctel')
                st.bar_chart(chart,width='stretch')
        else:
            st.info("No hay cócteles que coincidan con los filtros.")
        st.caption("Si un cóctel tiene ventas pero no tiene receta, aparece como alerta porque no es posible explicar su consumo de licor.")

    elif category_view=='Shots':
        st.markdown('<div class="ramona-section">🥃 Shots</div>',unsafe_allow_html=True)
        rows=shot_sales_summary(d1,d2)
        rows=_status_filter(rows,status_view)
        if rows:
            show=[{'Licor':r['Licor'],'Shots vendidos':f"{r['Shots vendidos']:.0f}",
                   'Oz / shot promedio':f"{r['Oz / shot promedio']:.2f}",
                   'Consumo teórico':f"{r['Consumo teórico']:.2f} oz",'Estado':r['Estado']} for r in rows]
            st.dataframe(pd.DataFrame(show),width='stretch',hide_index=True)
            chart=pd.DataFrame({'Licor':[r['Licor'] for r in rows],'Shots vendidos':[r['Shots vendidos'] for r in rows]}).set_index('Licor')
            st.bar_chart(chart,width='stretch')
        else:
            st.info("No hay ventas de shots que coincidan con los filtros en el periodo.")

    st.divider()
    st.markdown('<div class="ramona-section">🔎 Detalle para auditoría</div>',unsafe_allow_html=True)
    st.caption("Los registros son acumulativos: un nuevo cierre no elimina los anteriores. El ID de sesión, usuario y hora permiten reconstruir exactamente qué se ingresó y cuándo.")
    audit_mode=st.selectbox("Mostrar",['Actividad de inventario','Cierres','Histórico completo'],key='dash_audit_v6')
    types=['CLOSING'] if audit_mode=='Cierres' else (None if audit_mode=='Histórico completo' else ['CLOSING'])
    params=[d1.isoformat(),d2.isoformat()]
    type_sql=''
    if types:
        placeholders=','.join('?' for _ in types); type_sql=f" AND s.session_type IN ({placeholders})"; params.extend(types)
    raw=q(f"""SELECT s.id session_id,s.session_date,s.created_at,s.session_type,COALESCE(s.inventory_cycle,'DAILY') inventory_cycle,
                    s.paired_opening_session_id,p.id product_id,p.name product,c.name category,p.bottle_ml,
                    ic.qty_base,ic.qty_bottle_equiv,ic.variance,COALESCE(ic.observation,'') observation,u.name employee
             FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             JOIN products p ON p.id=ic.product_id JOIN categories c ON c.id=p.category_id
             LEFT JOIN users u ON u.id=s.user_id
             WHERE s.session_date BETWEEN ? AND ? {type_sql}
             ORDER BY s.created_at DESC,s.id DESC,p.name""",params)
    audit_rows=[]
    for r in raw:
        if r['category']=='Cerveza':
            count_text=f"{float(r['qty_base'] or 0):.0f} botellas"
        elif r['qty_bottle_equiv'] is not None:
            if r['bottle_ml']:
                count_text=f"{float(r['qty_bottle_equiv']):.2f} bot · {float(r['qty_base'] or 0):.2f} oz"
            else:
                count_text=f"{float(r['qty_bottle_equiv']):.2f} bot · oz pendiente"
        elif abs(float(r['qty_base'] or 0))>1e-9:
            count_text=f"{float(r['qty_base']):.2f} oz · registro histórico"
        else:
            count_text='0.00 bot · oz pendiente'
        audit_rows.append({'Sesión':int(r['session_id']),'Fecha':r['session_date'],'Hora local':format_local_time(r['created_at']),
                           'Tipo':'Apertura' if r['session_type']=='OPENING' else 'Cierre',
                           'Ciclo':'Semanal' if r['inventory_cycle']=='WEEKLY' else 'Diario','Producto':r['product'],
                           'Conteo registrado':count_text,'Empleado':r['employee'] or 'Usuario','Observación':r['observation']})
    if audit_rows:
        st.dataframe(pd.DataFrame(audit_rows),width='stretch',hide_index=True)
    else:
        st.info("No hay registros de inventario dentro del periodo seleccionado.")

    with st.expander("🧾 Historial íntegro de sesiones del periodo",expanded=False):
        sessions=q("""SELECT s.id,s.session_date,s.session_type,COALESCE(s.inventory_cycle,'DAILY') inventory_cycle,s.created_at,
                            s.paired_opening_session_id,u.name employee,COUNT(ic.id) item_count
                     FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                     LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                     WHERE s.session_date BETWEEN ? AND ?
                     GROUP BY s.id ORDER BY s.created_at DESC,s.id DESC""",(d1.isoformat(),d2.isoformat()))
        if sessions:
            hist=[]
            for r in sessions:
                hist.append({'ID sesión':int(r['id']),'Fecha':r['session_date'],'Hora local':format_local_time(r['created_at']),
                             'Tipo':'Apertura' if r['session_type']=='OPENING' else 'Cierre',
                             'Ciclo':'Semanal' if r['inventory_cycle']=='WEEKLY' else 'Diario','Usuario':r['employee'] or 'Usuario',
                             'Productos':int(r['item_count'] or 0),'Apertura vinculada':(int(r['paired_opening_session_id']) if r['paired_opening_session_id'] else '—')})
            st.dataframe(pd.DataFrame(hist),width='stretch',hide_index=True)
        else:
            st.info("Sin sesiones en el periodo.")

elif page=='Abastecimiento':
    page_header("Abastecimiento", "Consumo en oz y botellas equivalentes para convertir inventario operativo en compras.")
    st.caption("En licores, el control operativo se mantiene en oz y botellas equivalentes; las compras a proveedores se recomiendan siempre en botellas completas. En cerveza, las compras se expresan en unidades.")
    lookback=int(st.selectbox("Histórico para estimar consumo",[7,14,21,28,42,56],index=0,format_func=lambda x:f"Últimos {x} días")); safety=float(setting('safety_stock_pct','15'))/100
    st.caption("La recomendación de compra se proyecta para los próximos 7 días. Por defecto se usa el consumo de los últimos 7 días y puedes ampliar el histórico cuando necesites una tendencia más estable.")
    d2=local_today(); d1=d2-timedelta(days=lookback-1); data=consolidated(d1,d2); bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']
    rows=[]; products_to_buy=0; total_buy_units=0
    for r in data:
        p=r['_p']; complete=max(r['Días completos'],0); basis=r.get('_basis','unit' if p['category']=='Cerveza' else ('oz' if p['bottle_ml'] else 'bottle'))
        weekly=max((r['Consumo real']/complete*7) if complete else 0,0)
        sb,sbb=current_stock_basis(p,bar); sw,swb=current_stock_basis(p,wh)
        if sbb!=basis or swb!=basis:
            continue
        target=weekly*(1+safety); stock=max(sb+sw,0); need=max(target-stock,0)
        if p['category']=='Cerveza':
            buy=math.ceil(need) if need>0 else 0; buy_text=f"{buy} unidades"
        elif basis=='bottle':
            buy=math.ceil(need) if need>0 else 0; buy_text=f"{buy} botellas" if buy!=1 else "1 botella"
        else:
            boz=bottle_oz(p); buy=(math.ceil(need/boz) if need>0 and boz else 0); buy_text=(f"{buy} botellas" if buy!=1 else "1 botella")
        if buy and buy>0: products_to_buy+=1; total_buy_units+=buy
        rows.append({
            'Producto':product_label(p),
            'Consumo semanal':basis_qty_text(p,weekly,basis),
            'Stock Bar':basis_qty_text(p,sb,basis),
            'Stock Bodega':basis_qty_text(p,sw,basis),
            'Stock total':basis_qty_text(p,stock,basis),
            'Seguridad':f"{int(safety*100)}%",'Comprar':buy_text,'Días usados':complete,'_buy':buy or 0,'_stock':stock})
    if rows:
        k1,k2,k3=st.columns(3)
        k1.metric("Productos por reponer",products_to_buy)
        k2.metric("Margen de seguridad",f"{int(safety*100)}%")
        missing=sum(1 for x in rows if x['Comprar']=='⚠ Falta ml')
        k3.metric("Licores sin presentación",missing)
        df=pd.DataFrame(rows).sort_values(['_buy','Producto'],ascending=[False,True])
        df=df[(df['Días usados']>0) | (df['_stock']>0)].drop(columns=['_buy','_stock'])
        st.dataframe(df,width="stretch",hide_index=True,column_config={'Días usados':st.column_config.NumberColumn(format='%d')})
    else: st.info("Aún no hay suficiente información para estimar abastecimiento.")
    st.caption("En licores sin presentación en ml no se genera una compra estimada: primero debe completarse la presentación para convertir oz a botellas con precisión.")

elif page=='Reporte PDF':
    page_header("Reporte Ejecutivo", "Resumen gerencial para la propietaria, con métricas de decisión y detalle operativo.")
    st.caption("La primera página resume venta por conteo, ventas POS, diferencias, alertas, exactitud y abastecimiento. En licores se muestran oz y botellas equivalentes. Si falta un cierre anterior comparable o la confirmación POS, la comparación queda pendiente en lugar de generar alertas falsas.")
    a,b=st.columns(2)
    d1=a.date_input("Desde",value=local_today()-timedelta(days=6),key='pdf1')
    d2=b.date_input("Hasta",value=local_today(),key='pdf2')
    if d2<d1:
        st.error("La fecha Hasta no puede ser anterior a Desde.")
    else:
        inv_preview=_report_inventory_status(d1,d2)
        p1,p2,p3=st.columns(3)
        p1.metric("Estado del periodo",inv_preview['state'])
        p2.metric("Días comparables",inv_preview['complete_days'])
        p3.metric("Productos contados",inv_preview['products_counted'])
        can_download_report=can_download_executive_report(user)
        if can_download_report:
            if is_developer_user(user):
                st.caption("🔒 Descarga habilitada para la cuenta Developer/Owner.")
            else:
                st.caption("✅ Descarga habilitada: tu cuenta tiene autorización individual para el Reporte Ejecutivo.")
            if st.button("Generar reporte ejecutivo",type="primary"):
                try:
                    buf=build_executive_report_pdf(d1,d2)
                    st.success("Reporte ejecutivo generado. La primera página está diseñada para toma de decisiones; las páginas siguientes conservan el detalle operativo.")
                    st.download_button("Descargar Reporte Ejecutivo PDF",buf,file_name=f"la_ramona_reporte_ejecutivo_{d1}_{d2}.pdf",mime="application/pdf",width="stretch")
                except Exception as e:
                    st.error(f"No se pudo generar el reporte: {e}")
        else:
            st.info("🔒 Tu cuenta no tiene autorización para generar o descargar el Reporte Ejecutivo. El Developer/Owner puede habilitar este permiso individualmente desde Administración → Usuarios.")

elif page=='Administración':
    page_header("Configuración y administración", "Productos, recetas, usuarios, importaciones y parámetros del sistema.")
    t1,t2,t3,t4,t5=st.tabs(['Productos','Cócteles / Recetas','Usuarios','Importar Excel','Configuración'])
    with t1:
        st.subheader("Agregar / actualizar producto")
        cats=q("SELECT * FROM categories WHERE name IN ('Cerveza','Licor') ORDER BY name"); cm={r['name']:r['id'] for r in cats}; cat=st.selectbox("Categoría",list(cm)); name=st.text_input("Nombre del producto"); ml=st.number_input("Presentación (ml)",min_value=0.0,value=0.0,step=5.0); pkg=st.selectbox("Envase",['Botella','Lata','Otro'])
        principal_new=st.checkbox("Incluir este licor en el inventario diario",value=False,disabled=(cat!='Licor'),key='new_daily_liquor')
        if st.button("Agregar producto",type="primary") and name.strip():
            try:
                ex("INSERT INTO products(category_id,name,bottle_ml,package_type,daily_inventory) VALUES(?,?,?,?,?)",(cm[cat],name.strip(),ml or None,pkg,1 if (cat=='Licor' and principal_new) else 0)); st.success("Producto agregado."); st.rerun()
            except sqlite3.IntegrityError: st.error("Ese producto con la misma presentación ya existe.")
        st.caption("La presentación en ml puede completarse más adelante. Mientras esté pendiente, el inventario de licor se guarda como botellas completas + fracción; al registrar los ml, la app convierte automáticamente esos conteos a oz. El costo es opcional.")
        df=pd.read_sql_query("SELECT p.id ID,c.name Categoría,p.name Producto,p.bottle_ml 'ml',p.package_type Envase,p.unit_cost 'Costo por botella/unidad',CASE WHEN c.name='Cerveza' THEN 'Diario' WHEN p.daily_inventory=1 THEN 'Principal · Diario' ELSE 'Semanal' END 'Frecuencia inventario',p.active Activo FROM products p JOIN categories c ON c.id=p.category_id ORDER BY c.name,p.name",con)
        st.dataframe(df,width="stretch",hide_index=True)
        st.markdown("#### Licores principales del inventario diario")
        st.caption("Las cervezas siempre son diarias. Selecciona aquí qué licores deben aparecer también en el inventario diario; los demás aparecerán únicamente cuando selecciones inventario semanal.")
        liquor_rows=products('Licor')
        liquor_map={product_label(r):r for r in liquor_rows}
        selected_default=[label for label,r in liquor_map.items() if int(r['daily_inventory'] or 0)==1]
        selected_daily=st.multiselect("Licores principales",list(liquor_map.keys()),default=selected_default,key='daily_liquors_multiselect')
        if st.button("Guardar licores principales",width="stretch"):
            con.execute("UPDATE products SET daily_inventory=0 WHERE category_id=(SELECT id FROM categories WHERE name='Licor')")
            for label in selected_daily:
                con.execute("UPDATE products SET daily_inventory=1 WHERE id=?",(liquor_map[label]['id'],))
            con.commit(); backup_db(); st.success("Lista de licores principales actualizada."); st.rerun()
        st.markdown("#### Actualizar presentación / costo")
        st.caption("Selecciona el producto por su nombre. Ya no necesitas recordar ni escribir el ID interno.")
        update_rows=products(active=False)
        if not update_rows:
            st.info("No hay productos registrados para actualizar.")
        else:
            def update_product_label(r):
                ml_txt=f"{int(r['bottle_ml'])} ml" if r['bottle_ml'] else "ml pendiente"
                state_txt="" if int(r['active'] or 0)==1 else " · Inactivo"
                return f"{r['name']} · {r['category']} · {ml_txt}{state_txt}"

            update_map={update_product_label(r):r for r in update_rows}
            selected_product_label=st.selectbox(
                "Producto a actualizar",
                list(update_map.keys()),
                key='update_product_select'
            )
            selected_product=update_map[selected_product_label]
            pid=int(selected_product['id'])
            current_ml=float(selected_product['bottle_ml'] or 0.0)
            current_cost=float(selected_product['unit_cost'] or 0.0)

            info1,info2,info3=st.columns(3)
            info1.metric("Categoría",selected_product['category'])
            info2.metric("Presentación actual",f"{current_ml:g} ml" if current_ml>0 else "Pendiente")
            info3.metric("Costo actual",f"${current_cost:,.2f}" if current_cost>0 else "Pendiente")

            newml=st.number_input(
                "Nuevo ml",
                min_value=0.0,
                value=current_ml,
                step=5.0,
                key=f'updml_{pid}'
            )
            newcost=st.number_input(
                "Costo por botella/unidad ($, opcional)",
                min_value=0.0,
                value=current_cost,
                step=.01,
                key=f'updcost_{pid}'
            )
            if st.button("Actualizar presentación / costo",key='update_product_button'):
                ex("UPDATE products SET bottle_ml=?,unit_cost=? WHERE id=?",(newml or None,newcost or None,pid))
                if newml>0:
                    backfill_product_bottle_counts(pid)
                st.success(f"{selected_product['name']} actualizado. Si había conteos guardados por botellas, sus oz fueron recalculadas automáticamente.")
                st.rerun()

        st.markdown("---")
        st.markdown("### 🧹 Gestionar producto duplicado")
        st.caption("Solo Developer/Owner. La app revisa todas las relaciones antes de permitir borrar. Un conteo actual en 0 no basta por sí solo: se verifican también inventarios históricos, movimientos, POS y recetas.")
        if is_developer_user(user):
            all_catalog=products(active=False)
            # Detect likely duplicates using normalized category + name, while keeping presentation visible.
            dup_groups={}
            for r in all_catalog:
                key=(r['category'],normalized_text(r['name']))
                dup_groups.setdefault(key,[]).append(r)
            likely=[grp for grp in dup_groups.values() if len(grp)>1]
            if likely:
                dup_preview=[]
                for grp in likely:
                    dup_preview.append({
                        'Categoría':grp[0]['category'],
                        'Nombre':grp[0]['name'],
                        'Registros duplicados':len(grp),
                        'Presentaciones':' / '.join((f"{int(r['bottle_ml'])} ml" if r['bottle_ml'] else 'ml pendiente') for r in grp)
                    })
                st.warning(f"Se detectaron {len(likely)} nombre(s) posiblemente duplicados en el catálogo.")
                st.dataframe(pd.DataFrame(dup_preview),width='stretch',hide_index=True)
            else:
                st.info("No se detectan nombres duplicados exactos/normalizados en este momento. Igual puedes revisar cualquier producto manualmente.")

            dup_map={update_product_label(r):r for r in all_catalog}
            source_label=st.selectbox("Producto duplicado a revisar",list(dup_map.keys()),key='duplicate_source_product')
            source=dup_map[source_label]
            usage=product_usage_summary(source['id'])
            u1,u2,u3,u4,u5=st.columns(5)
            u1.metric("Conteos históricos",usage['inventory_rows'],delta=f"{usage['inventory_nonzero']} con valor")
            u2.metric("Movimientos",usage['movement_rows'],delta=f"{usage['movement_nonzero']} con valor")
            u3.metric("POS",usage['pos_rows'],delta=f"{usage['pos_nonzero']} con valor")
            u4.metric("Recetas",usage['recipe_rows'])
            u5.metric("Referencias totales",usage['total_rows'])

            if usage['safe_delete_unused']:
                st.success("✅ Este producto tiene 0 registros relacionados. Se puede eliminar definitivamente sin perder inventario, movimientos, POS ni recetas.")
                confirm_delete=st.text_input("Para eliminar escribe: ELIMINAR PRODUCTO",key='confirm_delete_unused')
                if st.button("Eliminar producto definitivamente",type='primary',disabled=(confirm_delete.strip().upper()!='ELIMINAR PRODUCTO'),key='delete_unused_product'):
                    ok,msg=delete_product_safely(source['id'],user['id'],allow_zero_references=False)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()
            elif usage['safe_delete_zero_only']:
                st.success("✅ El producto sí tiene filas históricas relacionadas, pero todas sus cantidades son 0 y no participa en recetas. Para un duplicado, la app puede limpiar únicamente esas referencias cero y eliminar el producto sin perder cantidades físicas o ventas.")
                st.caption("Esta acción sí cambia la auditoría de esas filas cero porque eran referencias del producto duplicado. La eliminación queda registrada en product_admin_audit y se respalda inmediatamente en Supabase.")
                confirm_zero=st.text_input("Para limpiar el duplicado escribe: ELIMINAR DUPLICADO CERO",key='confirm_delete_zero')
                if st.button("Eliminar duplicado con referencias en cero",type='primary',disabled=(confirm_zero.strip().upper()!='ELIMINAR DUPLICADO CERO'),key='delete_zero_product'):
                    ok,msg=delete_product_safely(source['id'],user['id'],allow_zero_references=True)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()
            else:
                st.warning("⚠️ Este producto tiene información con valor o participa en recetas. No se permite borrarlo directamente porque se perdería trazabilidad o se alterarían cálculos.")
                c1,c2=st.columns(2)
                if int(source['active'] or 0)==1:
                    if c1.button("Desactivar producto",key='deactivate_duplicate'):
                        try:
                            con.execute('BEGIN IMMEDIATE')
                            con.execute('UPDATE products SET active=0,daily_inventory=0 WHERE id=?',(int(source['id']),))
                            _audit_product_admin('DEACTIVATE',source,None,user['id'],json.dumps(usage,ensure_ascii=False))
                            con.commit(); backup_db(force=True); st.success("Producto desactivado. El historial permanece intacto y ya no aparecerá en nuevos registros."); st.rerun()
                        except Exception as e:
                            con.rollback(); st.error(f"No se pudo desactivar: {e}")
                else:
                    if c1.button("Reactivar producto",key='reactivate_duplicate'):
                        try:
                            con.execute('BEGIN IMMEDIATE')
                            con.execute('UPDATE products SET active=1 WHERE id=?',(int(source['id']),))
                            _audit_product_admin('REACTIVATE',source,None,user['id'],json.dumps(usage,ensure_ascii=False))
                            con.commit(); backup_db(force=True); st.success("Producto reactivado."); st.rerun()
                        except Exception as e:
                            con.rollback(); st.error(f"No se pudo reactivar: {e}")

                target_rows=[r for r in all_catalog if int(r['id'])!=int(source['id']) and r['category']==source['category']]
                if target_rows:
                    target_map={update_product_label(r):r for r in target_rows}
                    target_label=st.selectbox("Fusionar con el producto correcto",list(target_map.keys()),key='duplicate_target_product')
                    target=target_map[target_label]
                    conflicts=product_merge_conflicts(source['id'],target['id'])
                    if float(source['bottle_ml'] or 0)>0 and float(target['bottle_ml'] or 0)>0 and abs(float(source['bottle_ml'])-float(target['bottle_ml']))>1e-6:
                        st.error("Presentaciones diferentes: la fusión automática estará bloqueada para proteger la equivalencia histórica de botellas.")
                    elif conflicts['unsafe_inventory']:
                        st.error(f"Hay {len(conflicts['unsafe_inventory'])} sesión(es) donde ambos productos tienen conteos no cero. Requiere revisión manual antes de fusionar.")
                    elif conflicts['unsafe_recipes']:
                        st.error(f"Hay {len(conflicts['unsafe_recipes'])} receta(s) donde ambos productos tienen cantidades. Requiere revisión manual antes de fusionar.")
                    else:
                        st.info("La fusión reasignará conteos, movimientos, POS y recetas al producto correcto. Cualquier colisión histórica con cantidad 0 se elimina como marcador duplicado; luego el producto duplicado se retira.")
                        confirm_merge=st.text_input("Para fusionar escribe: FUSIONAR PRODUCTO",key='confirm_merge_product')
                        if st.button("Fusionar y retirar duplicado",disabled=(confirm_merge.strip().upper()!='FUSIONAR PRODUCTO'),key='merge_duplicate_product_button'):
                            ok,msg=merge_duplicate_product(source['id'],target['id'],user['id'])
                            (st.success if ok else st.error)(msg)
                            if ok: st.rerun()
        else:
            st.info("🔒 La eliminación, desactivación y fusión de productos duplicados está reservada a Developer/Owner.")
    with t2:
        st.subheader("Cócteles y recetas")
        st.caption("Las recetas se registran exclusivamente en onzas (oz) de licor por cóctel. Estas cantidades alimentan el consumo teórico del Dashboard cuando se registran las ventas del POS.")
        recipe_manual,recipe_excel,recipe_list=st.tabs(['✍️ Crear / editar receta','📥 Importar recetas Excel','📋 Recetas guardadas'])

        with recipe_manual:
            st.markdown("#### 1. Crear un cóctel nuevo")
            cnew1,cnew2=st.columns([3,1])
            cn=cnew1.text_input("Nombre del cóctel",key='recipe_new_cocktail_name')
            if cnew2.button("Crear cóctel",width='stretch',key='recipe_create_cocktail') and cn.strip():
                try:
                    ex("INSERT INTO cocktails(name) VALUES(?)",(cn.strip(),))
                    st.success("Cóctel creado. Ya puedes registrar su receta.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Ese cóctel ya existe.")

            cs=q("SELECT * FROM cocktails WHERE active=1 ORDER BY name")
            ls=products('Licor')
            if not cs:
                st.info("Primero crea al menos un cóctel.")
            elif not ls:
                st.warning("No hay licores activos en el catálogo. Agrégalos primero en Administración → Productos.")
            else:
                st.markdown("#### 2. Crear o modificar la receta")
                cmap={r['name']:r for r in cs}
                cocktail_name=st.selectbox("Cóctel",list(cmap.keys()),key='recipe_cocktail_select')
                cocktail=cmap[cocktail_name]
                current=q("""SELECT r.product_id,r.oz_qty,p.name product_name,p.bottle_ml,p.package_type
                             FROM recipes r JOIN products p ON p.id=r.product_id
                             WHERE r.cocktail_id=? ORDER BY p.name""",(cocktail['id'],))
                if current:
                    st.caption("Receta actual: " + " · ".join(f"{r['product_name']} {float(r['oz_qty']):g} oz" for r in current))
                else:
                    st.caption("Este cóctel todavía no tiene una receta registrada.")

                liquor_by_label={product_label(r):r for r in ls}
                liquor_labels=list(liquor_by_label.keys())
                current_by_pos=list(current)
                default_n=max(1,len(current_by_pos))
                ingredient_count=int(st.number_input("Número de licores en la receta",min_value=1,max_value=12,value=default_n,step=1,key=f"recipe_n_{cocktail['id']}"))
                recipe_rows=[]
                for i in range(ingredient_count):
                    c1,c2=st.columns([3,1])
                    default_label=liquor_labels[0]
                    default_oz=1.0
                    if i < len(current_by_pos):
                        saved=current_by_pos[i]
                        saved_row=next((r for r in ls if r['id']==saved['product_id']),None)
                        if saved_row:
                            default_label=product_label(saved_row)
                        default_oz=float(saved['oz_qty'])
                    idx=liquor_labels.index(default_label) if default_label in liquor_labels else 0
                    label=c1.selectbox(f"Licor {i+1}",liquor_labels,index=idx,key=f"recipe_liq_{cocktail['id']}_{i}")
                    oz=float(c2.number_input(f"Oz {i+1}",min_value=0.05,max_value=20.0,value=default_oz,step=0.25,format='%.2f',key=f"recipe_oz_{cocktail['id']}_{i}"))
                    recipe_rows.append((liquor_by_label[label]['id'],oz,label))

                st.caption("Guardar receta completa reemplaza la receta anterior de este cóctel por los ingredientes mostrados arriba.")
                if st.button("Guardar receta completa",type='primary',width='stretch',key=f"save_full_recipe_{cocktail['id']}"):
                    ids=[x[0] for x in recipe_rows]
                    if len(ids)!=len(set(ids)):
                        st.error("Un mismo licor aparece más de una vez. Selecciona cada licor una sola vez y suma sus onzas en un único ingrediente.")
                    else:
                        try:
                            con.execute("DELETE FROM recipes WHERE cocktail_id=?",(cocktail['id'],))
                            for pid,oz,_ in recipe_rows:
                                con.execute("INSERT INTO recipes(cocktail_id,product_id,oz_qty) VALUES(?,?,?)",(cocktail['id'],pid,oz))
                            con.commit(); backup_db()
                            st.success("Receta guardada correctamente en onzas de licor.")
                            st.rerun()
                        except Exception as e:
                            con.rollback(); st.error(f"No se pudo guardar la receta: {e}")

        with recipe_excel:
            st.markdown("#### Importar varias recetas desde Excel")
            st.caption("Puedes cargar un archivo .xlsx con una fila por ingrediente. Después seleccionas las columnas que corresponden a Cóctel, Licor y Oz; así no dependemos de nombres de columnas específicos.")
            recipe_file=st.file_uploader("Archivo de recetas (.xlsx)",type=['xlsx'],key='recipe_excel_upload')
            if recipe_file:
                try:
                    rxls=pd.ExcelFile(recipe_file)
                    rsheet=st.selectbox("Hoja con las recetas",rxls.sheet_names,key='recipe_sheet_select')
                    rdf=pd.read_excel(rxls,rsheet)
                    rdf=rdf.dropna(how='all')
                    if rdf.empty:
                        st.warning("La hoja seleccionada está vacía.")
                    else:
                        st.dataframe(rdf.head(20),width='stretch',hide_index=True)
                        cols=[str(c) for c in rdf.columns]
                        def guess_col(words,fallback=0):
                            for j,col in enumerate(cols):
                                k=normalized_text(col)
                                if any(w in k for w in words): return j
                            return min(fallback,len(cols)-1)
                        ic=guess_col(['coctel','cocktail','drink'],0)
                        il=guess_col(['licor','liquor','spirit','ingrediente'],1 if len(cols)>1 else 0)
                        io=guess_col(['oz','onza','ounce'],2 if len(cols)>2 else 0)
                        a,b,cx=st.columns(3)
                        cocktail_col=a.selectbox("Columna Cóctel",cols,index=ic,key='recipe_col_cocktail')
                        liquor_col=b.selectbox("Columna Licor",cols,index=il,key='recipe_col_liquor')
                        oz_col=cx.selectbox("Columna Oz",cols,index=io,key='recipe_col_oz')
                        if st.button("Importar recetas seleccionadas",type='primary',width='stretch',key='recipe_excel_import'):
                            imported=0; skipped=[]
                            try:
                                for row_idx,row in rdf.iterrows():
                                    cocktail_raw=str(row.get(cocktail_col,'') or '').strip()
                                    liquor_raw=str(row.get(liquor_col,'') or '').strip()
                                    oz_raw=pd.to_numeric(row.get(oz_col),errors='coerce')
                                    if not cocktail_raw and not liquor_raw: continue
                                    if not cocktail_raw or not liquor_raw or pd.isna(oz_raw) or float(oz_raw)<=0:
                                        skipped.append(f"Fila {row_idx+2}: faltan Cóctel, Licor u Oz válido")
                                        continue
                                    pmatch=recipe_product_match(liquor_raw)
                                    if not pmatch:
                                        skipped.append(f"Fila {row_idx+2}: licor no encontrado en catálogo → {liquor_raw}")
                                        continue
                                    con.execute("INSERT OR IGNORE INTO cocktails(name) VALUES(?)",(cocktail_raw,))
                                    cock=one("SELECT id FROM cocktails WHERE lower(name)=lower(?) ORDER BY id LIMIT 1",(cocktail_raw,))
                                    con.execute("""INSERT INTO recipes(cocktail_id,product_id,oz_qty) VALUES(?,?,?)
                                                   ON CONFLICT(cocktail_id,product_id) DO UPDATE SET oz_qty=excluded.oz_qty""",
                                                (cock['id'],pmatch['id'],float(oz_raw)))
                                    imported+=1
                                con.commit(); backup_db()
                                if imported: st.success(f"Importación terminada: {imported} ingredientes de receta guardados/actualizados.")
                                if skipped:
                                    st.warning(f"{len(skipped)} filas no se importaron para evitar inventar equivalencias.")
                                    with st.expander("Ver filas pendientes de revisión"):
                                        for msg in skipped[:100]: st.write("• "+msg)
                                if imported and not skipped: st.rerun()
                            except Exception as e:
                                con.rollback(); st.error(f"No se pudo completar la importación: {e}")
                except Exception as e:
                    st.error(f"No se pudo leer el archivo de recetas: {e}")

        with recipe_list:
            recipe_df=pd.read_sql_query("""SELECT c.name 'Cóctel',p.name 'Licor',r.oz_qty 'Oz de licor por cóctel'
                                         FROM recipes r JOIN cocktails c ON c.id=r.cocktail_id
                                         JOIN products p ON p.id=r.product_id
                                         WHERE c.active=1 ORDER BY c.name,p.name""",con)
            if recipe_df.empty:
                st.info("Todavía no hay recetas guardadas.")
            else:
                st.dataframe(recipe_df,width='stretch',hide_index=True)
                totals=recipe_df.groupby('Cóctel',as_index=False)['Oz de licor por cóctel'].sum().rename(columns={'Oz de licor por cóctel':'Total oz de licor'})
                st.markdown("#### Total de licor por cóctel")
                st.dataframe(totals,width='stretch',hide_index=True)
    with t3:
        st.subheader("Usuarios autorizados")
        st.caption("Solo los correos de esta lista con estado Activo pueden entrar con Google. Compartir el enlace no da acceso.")
        email=st.text_input("Correo Google / Gmail").strip().lower()
        un=st.text_input("Nombre del usuario")
        owner_email=normalized_email(secret_value('app','bootstrap_admin_email'))
        is_owner=normalized_email(user['email'])==owner_email
        assignable_roles=['STAFF','MANAGER','GENERAL_MANAGER','ADMIN'] if is_owner else ['STAFF','MANAGER','GENERAL_MANAGER']
        role=st.selectbox("Rol",assignable_roles,format_func=lambda x:ROLE_LABELS.get(x,x))
        report_access_new=False
        if is_owner:
            report_access_new=st.checkbox("Autorizar generación y descarga del Reporte Ejecutivo al crear este usuario",value=False,key="new_user_report_access")
            st.caption("Este permiso es independiente del rol. Para usarlo, el usuario también debe tener acceso a la sección Reporte PDF (MANAGER, MANAGER GENERAL o ADMIN).")
        st.caption("MANAGER y MANAGER GENERAL pueden administrar productos, recetas, usuarios y configuración operativa. El reinicio total sigue reservado a ADMIN. Solo la cuenta Developer/Owner configurada puede otorgar o modificar el rol ADMIN y autorizar la descarga del Reporte Ejecutivo.")
        if st.button("Autorizar usuario",type="primary",width="stretch"):
            if not email or '@' not in email:
                st.error("Ingresa un correo válido.")
            else:
                existing=one("SELECT * FROM users WHERE lower(email)=?",(email,))
                if existing and existing['role']=='ADMIN' and not is_owner:
                    st.error("Solo la cuenta Developer/Owner puede modificar un usuario ADMIN.")
                elif existing:
                    ex("UPDATE users SET name=?,role=?,active=1 WHERE id=?",(un.strip() or existing['name'],role,existing['id']))
                    st.success("Usuario actualizado y activado. El permiso de Reporte Ejecutivo se conserva; puedes cambiarlo abajo en Gestionar usuario."); st.rerun()
                else:
                    base_name=un.strip() or email.split('@')[0]
                    candidate=base_name; i=2
                    while one("SELECT 1 FROM users WHERE name=?",(candidate,)):
                        candidate=f"{base_name} {i}"; i+=1
                    ex("INSERT INTO users(name,pin_hash,email,role,active,report_access,created_at) VALUES(?,?,?,?,1,?,?)",(candidate,'',email,role,1 if (is_owner and report_access_new) else 0,now_iso()))
                    st.success("Correo autorizado. Ya puede entrar con Google."); st.rerun()
        users_df=pd.read_sql_query("SELECT id ID,name Nombre,email Email,CASE role WHEN 'GENERAL_MANAGER' THEN 'MANAGER GENERAL' ELSE role END Rol,CASE active WHEN 1 THEN 'Activo' ELSE 'Bloqueado' END Estado,report_access '_report_access',last_login_at 'Último acceso' FROM users WHERE email IS NOT NULL AND email<>'' ORDER BY active DESC,role,name",con)
        if not users_df.empty:
            users_df['Reporte Ejecutivo']=users_df.apply(lambda r: 'Developer/Owner' if normalized_email(r['Email'])==owner_email else ('Autorizado' if int(r['_report_access'] or 0)==1 else 'Sin acceso'),axis=1)
            users_df=users_df.drop(columns=['_report_access'])
            if 'Último acceso' in users_df.columns:
                users_df['Último acceso']=users_df['Último acceso'].apply(lambda x: format_local_datetime(x, '%Y-%m-%d %I:%M %p') if pd.notna(x) and x else '—')
        st.dataframe(users_df,width="stretch",hide_index=True)
        if is_owner:
            manageable=q("SELECT id,name,email,role,active,report_access FROM users WHERE email IS NOT NULL AND email<>'' ORDER BY name")
        else:
            manageable=q("SELECT id,name,email,role,active,report_access FROM users WHERE email IS NOT NULL AND email<>'' AND role<>'ADMIN' ORDER BY name")
        if manageable:
            labels={f"{r['name']} · {r['email']} · {ROLE_LABELS.get(r['role'],r['role'])} · {'Activo' if r['active'] else 'Bloqueado'}":r for r in manageable}
            sel=st.selectbox("Gestionar usuario",list(labels.keys()))
            target=labels[sel]
            c1,c2=st.columns(2)
            if target['active']:
                if c1.button("Bloquear acceso",width="stretch"):
                    if target['id']==user['id']:
                        st.error("No puedes bloquear tu propia cuenta mientras estás conectado.")
                    else:
                        ex("UPDATE users SET active=0 WHERE id=?",(target['id'],)); st.success("Usuario bloqueado."); st.rerun()
            else:
                if c1.button("Reactivar acceso",width="stretch"):
                    ex("UPDATE users SET active=1 WHERE id=?",(target['id'],)); st.success("Usuario reactivado."); st.rerun()
            role_options=['STAFF','MANAGER','GENERAL_MANAGER','ADMIN'] if is_owner else ['STAFF','MANAGER','GENERAL_MANAGER']
            current_role=target['role'] if target['role'] in role_options else role_options[0]
            new_role=c2.selectbox("Cambiar rol",role_options,index=role_options.index(current_role),format_func=lambda x:ROLE_LABELS.get(x,x),key='manage_role')
            if c2.button("Guardar rol",width="stretch"):
                if target['id']==user['id'] and new_role!=target['role']:
                    st.warning("Estás cambiando tu propio rol. El cambio se aplicará inmediatamente al recargar.")
                ex("UPDATE users SET role=? WHERE id=?",(new_role,target['id'])); st.success("Rol actualizado."); st.rerun()

            if is_owner:
                st.markdown("#### Acceso al Reporte Ejecutivo")
                target_is_owner=normalized_email(target['email'])==owner_email
                current_report_access=True if target_is_owner else bool(int(target['report_access'] or 0))
                allow_report=st.checkbox(
                    "Permitir generar y descargar el Reporte Ejecutivo",
                    value=current_report_access,
                    disabled=target_is_owner,
                    key=f"report_access_{target['id']}"
                )
                if target_is_owner:
                    st.caption("La cuenta Developer/Owner siempre tiene acceso y no puede perder este permiso.")
                else:
                    st.caption("Permiso individual administrado únicamente por Developer/Owner. Es independiente del rol del usuario.")
                    if st.button("Guardar acceso al reporte",width="stretch",key=f"save_report_access_{target['id']}"):
                        ex("UPDATE users SET report_access=? WHERE id=?",(1 if allow_report else 0,target['id']))
                        st.success("Acceso al Reporte Ejecutivo actualizado."); st.rerun()
    with t4:
        st.subheader("Importar catálogo / recetas / ventas desde Excel")
        st.caption("Carga una exportación .xlsx del Google Sheet. Se importa solo información estructurada; los registros ambiguos se dejan para revisión y no se inventan datos.")
        up=st.file_uploader("Archivo Excel",type=['xlsx'])
        if up:
            try:
                xls=pd.ExcelFile(up)
                st.write("Hojas detectadas:",", ".join(xls.sheet_names))
                if st.button("Importar datos reconocibles",type="primary"):
                    imported=0
                    if 'PRODUCTOS' in xls.sheet_names:
                        dfp=pd.read_excel(xls,'PRODUCTOS')
                        for _,r in dfp.dropna(subset=['Producto']).iterrows():
                            cat=str(r.get('Categoría','Licor')).strip() or 'Licor'; cid=one("SELECT id FROM categories WHERE name=?",(cat,));
                            if not cid: continue
                            mlv=pd.to_numeric(r.get('Tamaño botella (ml)'),errors='coerce'); mlv=None if pd.isna(mlv) else float(mlv)
                            try: con.execute("INSERT OR IGNORE INTO products(category_id,name,bottle_ml,package_type) VALUES(?,?,?,'Botella')",(cid['id'],str(r['Producto']).strip(),mlv)); imported+=1
                            except: pass
                    if 'RECETAS' in xls.sheet_names:
                        dfr=pd.read_excel(xls,'RECETAS')
                        for _,r in dfr.dropna(subset=['Cóctel','Licor']).iterrows():
                            cr=str(r['Cóctel']).strip(); lr=str(r['Licor']).strip(); oz=pd.to_numeric(r.get('Oz por cóctel'),errors='coerce')
                            if pd.isna(oz): continue
                            con.execute("INSERT OR IGNORE INTO cocktails(name) VALUES(?)",(cr,)); c=one("SELECT id FROM cocktails WHERE name=?",(cr,)); p=one("SELECT id FROM products WHERE lower(name)=lower(?) ORDER BY id LIMIT 1",(lr,))
                            if c and p: con.execute("INSERT INTO recipes(cocktail_id,product_id,oz_qty) VALUES(?,?,?) ON CONFLICT(cocktail_id,product_id) DO UPDATE SET oz_qty=excluded.oz_qty",(c['id'],p['id'],float(oz))); imported+=1
                    con.commit(); backup_db(); st.success(f"Importación terminada. Registros procesados: {imported}"); st.rerun()
            except Exception as e: st.error(f"No se pudo leer el archivo: {e}")
    with t5:
        st.subheader("Estado de sincronización")
        local_sync_h=_sqlite_health(DB)
        local_sync_digest=_db_data_digest(DB)
        remote_sync_h=None; remote_sync_digest=None; remote_sync_rev=None
        if _supabase_ready():
            _tmp_sync=None
            try:
                _tmp_sync,remote_sync_h,remote_sync_digest,_m_sync=_remote_revision_to_temp()
                remote_sync_rev=(_m_sync.get('revision') if _m_sync else None)
            except Exception as _e:
                st.warning(f"No se pudo leer el estado remoto en este momento: {_e}")
            finally:
                if _tmp_sync:
                    try: os.remove(_tmp_sync)
                    except Exception: pass
        if remote_sync_h and remote_sync_h.get('valid'):
            same=(local_sync_digest==remote_sync_digest)
            c1,c2=st.columns(2)
            c1.info(f"Local · {local_sync_h['products']} productos · diario {local_sync_h['inventory_sessions']} sesiones/{local_sync_h['inventory_counts']} conteos · semanal {local_sync_h['weekly_inventory_sessions']} sesiones/{local_sync_h['weekly_inventory_counts']} conteos · {local_sync_h['movements']} movimientos · {local_sync_h['pos_sales']} POS")
            c2.info(f"Supabase · {remote_sync_h['products']} productos · diario {remote_sync_h['inventory_sessions']} sesiones/{remote_sync_h['inventory_counts']} conteos · semanal {remote_sync_h['weekly_inventory_sessions']} sesiones/{remote_sync_h['weekly_inventory_counts']} conteos · {remote_sync_h['movements']} movimientos · {remote_sync_h['pos_sales']} POS")
            if same:
                st.success(f"✅ Sincronizado · revisión {(remote_sync_rev or 'legacy')[:8]} · huella {local_sync_digest[:12]}")
            else:
                st.error("⚠️ Local y Supabase NO contienen los mismos datos. No realices nuevas capturas hasta revisar Recuperación de base de datos. La protección V0.5.9 impide sobrescribir automáticamente una rama divergente.")
        elif _supabase_ready():
            st.warning("Supabase está configurado, pero todavía no se pudo validar una revisión durable remota.")
        st.caption(f"Preflight de esta ejecución: {SYNC_PREFLIGHT_STATUS.get('status')} · {SYNC_PREFLIGHT_STATUS.get('message','')}")
        st.divider()

        st.subheader("Respaldo automático")
        scfg=_supabase_cfg()
        if _supabase_ready():
            last=st.session_state.get('_last_supabase_backup','Aún no realizado en esta sesión')
            st.success(f"Supabase Storage configurado · último backup en esta sesión: {last}")
            st.caption("Cada escritura confirmada crea primero una revisión inmutable y verificada en `revisions_v2/`. Solo después se actualizan `latest`, el diario y el semanal como copias de conveniencia. La recuperación usa siempre la revisión inmutable más reciente, evitando caché obsoleta y sobrescrituras accidentales.")
            if st.button("Crear / verificar backup ahora en Supabase",width="stretch",key='supabase_backup_now'):
                ok,msg=backup_db_to_supabase(force=True); (st.success if ok else st.error)(msg)
            if st.session_state.get('_supabase_backup_error'):
                st.warning("Último error de Supabase: "+st.session_state['_supabase_backup_error'])
        else:
            st.warning("Supabase backup no está configurado. Revisa [supabase_backup] en Streamlit Secrets.")

        if os.path.exists(DB):
            with open(DB,'rb') as fh:
                st.download_button("Descargar copia manual de la base SQLite",data=fh.read(),file_name=f"bar_inventory_backup_{local_today().isoformat()}.db",mime="application/octet-stream",width="stretch")

        with st.expander("Google Drive (configuración anterior / contingencia)"):
            cfg=_gdrive_cfg()
            if cfg['enabled'] and cfg['folder_id'] and cfg['service_account_json']:
                st.caption("La configuración anterior se conserva, pero Supabase es el respaldo primario de esta versión.")
                if st.button("Probar respaldo legacy en Google Drive",width="stretch",key='drive_legacy_backup'):
                    ok,msg=backup_db_to_drive(force=True); (st.success if ok else st.error)(msg)
            else:
                st.caption("Google Drive no configurado. No es necesario para usar Supabase.")
        st.divider()
        owner_for_correction=normalized_email(user['email'])==normalized_email(secret_value('app','bootstrap_admin_email'))
        if owner_for_correction:
            st.subheader("Recuperación de base de datos")
            st.caption("Solo Developer/Owner. Permite validar y restaurar un respaldo SQLite completo sin volver a desplegar código. Antes de reemplazar la base se conserva una copia local de contingencia.")
            current_health=_sqlite_health(DB)
            if current_health['valid']:
                st.info(f"Base actual: {current_health['active_users']}/{current_health['users']} usuarios activos · {current_health['products']} productos · diario {current_health['inventory_sessions']} sesiones/{current_health['inventory_counts']} conteos · semanal {current_health['weekly_inventory_sessions']} sesiones/{current_health['weekly_inventory_counts']} conteos · {current_health['movements']} movimientos · {current_health['pos_sales']} filas POS.")
            else:
                st.warning(f"La base actual no supera la validación: {current_health['reason']}")
            if _supabase_ready():
                st.markdown("##### Restaurar `latest` desde Supabase")
                if st.button("Verificar último backup de Supabase",width='stretch',key='check_supabase_latest'):
                    tmp_latest=None
                    try:
                        tmp_latest,h=restore_latest_from_supabase_to_temp()
                        st.session_state['_supabase_latest_health']=h
                        st.success(f"Latest válido: {h['active_users']}/{h['users']} usuarios activos · {h['products']} productos · diario {h['inventory_sessions']} sesiones/{h['inventory_counts']} conteos · semanal {h['weekly_inventory_sessions']} sesiones/{h['weekly_inventory_counts']} conteos · {h['movements']} movimientos · {h['pos_sales']} filas POS · rev {(h.get('revision') or 'legacy')[:8]} · huella {(h.get('data_digest') or '')[:12]}.")
                    except Exception as e:
                        st.error(f"No se pudo verificar latest: {e}")
                    finally:
                        if tmp_latest:
                            try: os.remove(tmp_latest)
                            except Exception: pass
                latest_confirm=st.text_input("Para restaurar latest escribe: RESTAURAR SUPABASE",key='supabase_restore_confirm')
                if st.button("Restaurar latest de Supabase",type='secondary',width='stretch',key='restore_supabase_latest'):
                    if latest_confirm.strip()!='RESTAURAR SUPABASE':
                        st.error("Confirmación incorrecta. Escribe exactamente: RESTAURAR SUPABASE")
                    else:
                        tmp_latest=None
                        try:
                            tmp_latest,h=restore_latest_from_supabase_to_temp()
                            if not tmp_latest or not h['valid']:
                                raise RuntimeError(h.get('reason','backup inválido'))
                            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                            pre=f"bar_inventory_v3_before_supabase_restore_{stamp}.db"
                            con.commit()
                            if os.path.exists(DB): shutil.copy2(DB,pre)
                            con.close(); _atomic_replace_db(tmp_latest,'manual_supabase_restore')
                            st.success("Último backup de Supabase restaurado y validado. La aplicación se recargará.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo restaurar latest de Supabase: {e}")
                        finally:
                            if tmp_latest:
                                try: os.remove(tmp_latest)
                                except Exception: pass
                st.divider()
            restore_upload=st.file_uploader("Seleccionar respaldo SQLite (.db)",type=['db','sqlite','sqlite3'],key='db_restore_upload')
            if restore_upload is not None:
                raw_restore=restore_upload.getvalue()
                fd,tmp_restore=tempfile.mkstemp(prefix='ramona_restore_',suffix='.db')
                os.close(fd)
                with open(tmp_restore,'wb') as fh:
                    fh.write(raw_restore)
                candidate=_sqlite_health(tmp_restore)
                if not candidate['valid']:
                    st.error(f"El archivo no es un respaldo válido de La Ramona: {candidate['reason']}")
                else:
                    st.success(f"Respaldo válido: {candidate['active_users']}/{candidate['users']} usuarios activos · {candidate['products']} productos · {candidate['inventory_sessions']} sesiones · {candidate['inventory_counts']} conteos · {candidate['movements']} movimientos · {candidate['pos_sales']} filas POS.")
                    restore_confirm=st.text_input("Para restaurar escribe exactamente: RESTAURAR BASE",key='db_restore_confirm')
                    if st.button("Restaurar este respaldo",type='secondary',width='stretch',key='db_restore_apply'):
                        if restore_confirm.strip()!='RESTAURAR BASE':
                            st.error("Confirmación incorrecta. Escribe exactamente: RESTAURAR BASE")
                        else:
                            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                            pre=f"bar_inventory_v3_before_manual_restore_{stamp}.db"
                            try:
                                con.commit()
                                if os.path.exists(DB): shutil.copy2(DB,pre)
                                con.close()
                                _atomic_replace_db(tmp_restore,'manual_restore')
                                st.success("Base restaurada. La aplicación se recargará con usuarios, productos e historial del respaldo.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"No se pudo restaurar la base: {e}")
                try: os.remove(tmp_restore)
                except Exception: pass
            st.divider()
        if owner_for_correction:
            st.subheader("Carga histórica de Cierre diario")
            st.caption("Solo Developer/Owner. Transcribe cierres físicos conservados en papel sin alterar el flujo activo. Desde V0.6.0 los cálculos operativos usan cierre contra cierre; no es necesario reconstruir aperturas para los nuevos indicadores.")
            h1,h2=st.columns(2)
            hist_date=h1.date_input("Fecha operativa histórica",value=max(local_today()-timedelta(days=1),date(2026,1,1)),max_value=local_today(),key='hist_inventory_date')
            h2.text_input("Tipo de registro",value='Cierre diario',disabled=True,key='hist_inventory_type_fixed')
            hist_kind='CLOSING';hist_cycle='DAILY'
            hist_scope=st.radio("Productos a transcribir",['Todo el inventario','Solo cervezas','Solo licores'],horizontal=True,key='hist_inventory_scope')
            hist_users=q("SELECT id,name,email FROM users WHERE active=1 ORDER BY name")
            hist_operator=st.selectbox("Responsable indicado en el registro de papel (opcional)",['No especificado']+[f"{r['name']} · {r['email']}" for r in hist_users],key='hist_original_operator')
            hist_source=st.text_input("Fuente / referencia (opcional)",value="Registro en papel",key='hist_source_note')
            hist_general=st.text_area("Observación histórica (opcional)",key='hist_general_note')
            hist_bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
            hist_ps=inventory_products('DAILY')
            if hist_scope=='Solo cervezas':hist_ps=[p for p in hist_ps if p['category']=='Cerveza']
            elif hist_scope=='Solo licores':hist_ps=[p for p in hist_ps if p['category']=='Licor']
            existing_hist=q("""SELECT s.id,s.created_at,u.name employee,COUNT(ic.id) item_count
                               FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                               LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                               WHERE s.session_date=? AND s.session_type='CLOSING' AND COALESCE(s.inventory_cycle,'DAILY')='DAILY'
                               GROUP BY s.id ORDER BY s.created_at DESC,s.id DESC""",(hist_date.isoformat(),))
            if existing_hist:
                st.warning(f"Ya existen {len(existing_hist)} captura(s) de Cierre para esta fecha. La nueva captura no borra las anteriores; queda registrada para auditoría y la captura más reciente por producto será la referencia de esa fecha.")
            hist_counts=[]
            for cat in ['Cerveza','Licor']:
                group=[p for p in hist_ps if p['category']==cat]
                if group:st.markdown(f"##### {cat}")
                for p in group:
                    prev,prev_beq,prev_date=last_close_detail(p['id'],hist_bar,(hist_date-timedelta(days=1)).isoformat())
                    default=float(prev or 0);default_beq=prev_beq
                    ref_txt=(f"Cierre anterior ({prev_date}): {_count_text(p,prev,prev_beq)}" if prev is not None or prev_beq is not None else "Sin cierre anterior registrado")
                    with st.expander(product_label(p),expanded=True):
                        st.info("📌 "+ref_txt)
                        rr=bottle_count_input(p,f"hist_close_{hist_date}_{p['id']}",default,default_beq)
                        hist_counts.append({'pid':p['id'],'lid':hist_bar,'qty':rr['base'],'prev':None,'var':None,'obs':'','bottle_equiv':rr['bottles'],'name':p['name'],'category':p['category']})
            st.caption("Los valores digitados, incluidos los ceros, se guardarán exactamente como aparecen en el registro físico en papel.")
            hist_ack=st.checkbox("Confirmo que este cierre fue realizado físicamente y quedó registrado en papel debido a una contingencia del sistema, y que los valores digitados corresponden al registro físico.",key='hist_ack')
            if st.button("Guardar cierre histórico",type='secondary',width='stretch',key='save_historical_inventory'):
                if not hist_ack:
                    st.error("Debes confirmar que el cierre físico quedó registrado en papel y que los valores digitados corresponden a ese registro.")
                else:
                    operator_txt=hist_operator if hist_operator!='No especificado' else 'No especificado'
                    audit=f"[TRANSCRIPCIÓN HISTÓRICA POR CONTINGENCIA ingresada por Developer/Owner el {local_now().strftime('%d/%m/%Y %I:%M:%S %p')} · Responsable reportado: {operator_txt} · Fuente: {hist_source or 'Registro en papel'} · Modelo cierre-contra-cierre V0.6.0]"
                    full_notes=(audit+("\n"+hist_general.strip() if hist_general.strip() else '')).strip()
                    result=save_historical_session('CLOSING',hist_counts,hist_date,full_notes,'DAILY',None)
                    if not result.get('ok'):st.error(result.get('error','No se pudo guardar el cierre histórico.'))
                    else:
                        detail=("La captura ya existía y no se duplicó." if result.get('duplicate') else f"{len(hist_counts)} productos transcritos. El historial anterior se conserva.")
                        if result.get('saved'):detail += ("  \nRespaldo automático: **✅ Supabase actualizado**." if result.get('backup_ok') else f"  \n⚠️ Cierre histórico guardado en SQLite; backup: {result.get('backup_message','pendiente')}")
                        title=("Cierre histórico guardado y respaldado" if result.get('backup_ok',True) else "Cierre histórico guardado; respaldo pendiente")
                        st.session_state['_inventory_flash']={'level':('success' if result.get('backup_ok',True) else 'warning'),'message':operation_confirmation(title,hist_date,detail,result.get('created_at'))};st.rerun()
            st.divider()

        if owner_for_correction:
            st.subheader("Corrección controlada de una captura")
            st.caption("Herramienta de contingencia para corregir una captura guardada con tipo o fecha operativa incorrectos. No elimina conteos, usuario ni hora original; solo reclasifica la sesión y deja trazabilidad en Observaciones.")
            recent_sessions=q("""SELECT s.id,s.session_date,s.session_type,COALESCE(s.inventory_cycle,'DAILY') inventory_cycle,
                                      s.created_at,COALESCE(s.notes,'') notes,u.name employee,COUNT(ic.id) item_count
                               FROM inventory_sessions s LEFT JOIN users u ON u.id=s.user_id
                               LEFT JOIN inventory_counts ic ON ic.session_id=s.id
                               GROUP BY s.id ORDER BY s.created_at DESC,s.id DESC LIMIT 20""")
            if recent_sessions:
                session_labels={f"ID {r['id']} · {'Apertura' if r['session_type']=='OPENING' else 'Cierre'} · {r['session_date']} · {format_local_time(r['created_at'])} · {r['employee'] or 'Usuario'} · {int(r['item_count'] or 0)} productos":r for r in recent_sessions}
                corr_label=st.selectbox("Captura a corregir",list(session_labels.keys()),key='session_correction_select')
                corr=session_labels[corr_label]
                cc1,cc2=st.columns(2)
                corrected_type=cc1.selectbox("Tipo correcto",['OPENING','CLOSING'],index=(0 if corr['session_type']=='OPENING' else 1),format_func=lambda x:'Apertura' if x=='OPENING' else 'Cierre',key='session_correction_type')
                corrected_date=cc2.date_input("Fecha operativa correcta",value=date.fromisoformat(corr['session_date']),key='session_correction_date')
                st.info(f"La hora real del registro se conservará: {format_local_datetime(corr['created_at'],'%d/%m/%Y %I:%M %p')}.")
                corr_confirm=st.text_input(f"Para aplicar escribe: CORREGIR {corr['id']}",key='session_correction_confirm')
                if st.button("Aplicar corrección de captura",type='secondary',width='stretch',key='apply_session_correction'):
                    if corr_confirm.strip()!=f"CORREGIR {corr['id']}":
                        st.error(f"Confirmación incorrecta. Escribe exactamente: CORREGIR {corr['id']}")
                    else:
                        new_ds=corrected_date.isoformat(); cycle=str(corr['inventory_cycle'] or 'DAILY'); paired=None
                        if corrected_type=='CLOSING':
                            # Legacy link is optional from V0.6.0; close-only reconciliation does not depend on OPENING.
                            opening_candidate=_inventory_session(new_ds,'OPENING',cycle,corr['created_at'])
                            paired=int(opening_candidate['id']) if opening_candidate else None
                        stamp=local_now().strftime('%d/%m/%Y %I:%M %p')
                        audit_note=f"[CORRECCIÓN Developer/Owner {stamp}: {corr['session_type']} {corr['session_date']} → {corrected_type} {new_ds}]"
                        notes=(str(corr['notes'] or '').strip()+"\n"+audit_note).strip()
                        con.execute("UPDATE inventory_sessions SET session_date=?,session_type=?,paired_opening_session_id=?,notes=? WHERE id=?",(new_ds,corrected_type,paired,notes,corr['id']))
                        con.commit(); backup_db()
                        st.success("Captura reclasificada sin borrar conteos, usuario ni timestamp original. Revisa el Dashboard y Detalle para auditoría.")
                        st.rerun()
            else:
                st.info("No hay sesiones para corregir.")
            st.divider()
        if user['role']=='ADMIN':
            st.subheader("Inicio de operación / limpiar datos históricos")
            st.caption("Solo ADMIN puede ejecutar este reinicio. La herramienta elimina datos transaccionales anteriores: inventarios, POS/ventas y movimientos. Conserva productos, categorías, presentaciones, recetas, usuarios, roles y configuración.")
            inv_sessions=one("SELECT COUNT(*) n FROM inventory_sessions")['n']
            inv_counts=one("SELECT COUNT(*) n FROM inventory_counts")['n']
            weekly_sessions=one("SELECT COUNT(*) n FROM weekly_inventory_sessions")['n']
            weekly_counts=one("SELECT COUNT(*) n FROM weekly_inventory_counts")['n']
            pos_rows=one("SELECT COUNT(*) n FROM pos_sales")['n']
            mov_rows=one("SELECT COUNT(*) n FROM movements")['n']
            st.info(f"Datos actuales: diario {inv_sessions} sesiones/{inv_counts} conteos · semanal {weekly_sessions} sesiones/{weekly_counts} conteos · {pos_rows} registros POS/ventas · {mov_rows} movimientos.")
            confirm_reset=st.text_input("Para confirmar escribe exactamente: INICIAR DESDE CERO",key="reset_inventory_confirm")
            if st.button("Dejar operación en cero",type="secondary",width="stretch"):
                if confirm_reset.strip() != "INICIAR DESDE CERO":
                    st.error("Confirmación incorrecta. Escribe exactamente: INICIAR DESDE CERO")
                else:
                    try:
                        con.execute("DELETE FROM weekly_inventory_counts")
                        con.execute("DELETE FROM weekly_inventory_captures")
                        con.execute("DELETE FROM weekly_inventory_session_products")
                        con.execute("DELETE FROM weekly_inventory_sessions")
                        con.execute("DELETE FROM inventory_counts")
                        con.execute("DELETE FROM inventory_sessions")
                        con.execute("DELETE FROM pos_sales")
                        con.execute("DELETE FROM pos_batches")
                        con.execute("DELETE FROM movements")
                        con.execute("INSERT INTO settings(key,value) VALUES('sheet_history_seeded','1') ON CONFLICT(key) DO UPDATE SET value='1'")
                        con.execute("INSERT INTO settings(key,value) VALUES('production_inventory_started_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(now_iso(),))
                        con.commit()
                        backup_db()
                        st.success("Operación reiniciada en cero. Se eliminaron inventarios diarios y semanales, POS/ventas y movimientos anteriores. Productos, recetas, usuarios, roles y configuración permanecen intactos. El próximo conteo será la nueva línea base.")
                        st.rerun()
                    except Exception as e:
                        con.rollback()
                        st.error(f"No se pudo limpiar los datos históricos: {e}")
            st.divider()
        else:
            st.info("Puedes usar las demás opciones de Administración. El reinicio total de datos operativos está reservado exclusivamente para ADMIN.")
            st.divider()
        safety=st.number_input("Stock de seguridad para abastecimiento (%)",min_value=0,max_value=100,value=int(float(setting('safety_stock_pct','15'))),step=1)
        tb=st.number_input("Tolerancia cerveza (botellas)",min_value=0.0,value=float(setting('tolerance_beer','1')),step=.5)
        tl=st.number_input("Tolerancia licor (oz)",min_value=0.0,value=float(setting('tolerance_liquor','1')),step=.25)
        if st.button("Guardar configuración",type="primary"):
            for k,v in [('safety_stock_pct',safety),('tolerance_beer',tb),('tolerance_liquor',tl)]: con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,str(v)))
            con.commit(); backup_db(); st.success("Configuración guardada.")
