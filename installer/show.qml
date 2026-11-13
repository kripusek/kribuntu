import QtQuick 2.0
import calamares.slideshow 1.0
Presentation {
    Slide {
        Rectangle {
            width: parent.masterWidth
            height: parent.masterHeight
            color: "#14141b"
            Image { anchors.fill: parent; source: "kribuntu-wallpaper.png"; fillMode: Image.PreserveAspectCrop; opacity: 0.45 }
            Column {
                anchors.left: parent.left; anchors.leftMargin: 48
                anchors.verticalCenter: parent.verticalCenter; spacing: 20
                Text { text: "KRIBUNTU"; color: "white"; font.pixelSize: 52; font.bold: true }
                Text { text: "Twoj system. Twoje gry."; color: "#ff596d"; font.pixelSize: 24 }
                Text { text: "Trwa instalacja. Dziekujemy za cierpliwosc."; color: "white"; font.pixelSize: 18 }
            }
        }
    }
}
