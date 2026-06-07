#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
import sensor_msgs_py.point_cloud2 as pc2


class VelodyneToAutoware(Node):
    def __init__(self):
        super().__init__("velodyne_to_autoware")

        self.sub = self.create_subscription(
            PointCloud2,
            "/velodyne_points",
            self.callback,
            10,
        )

        self.pub = self.create_publisher(
            PointCloud2,
            "/sensing/lidar/concatenated/pointcloud",
            10,
        )

        self.get_logger().info(
            "Converting /velodyne_points → /sensing/lidar/concatenated/pointcloud"
        )

    def callback(self, msg: PointCloud2):
        points = []

        for p in pc2.read_points(
            msg,
            field_names=("x", "y", "z", "intensity", "ring"),
            skip_nans=True,
        ):
            x, y, z, intensity, ring = p

            intensity_u8 = max(0, min(255, int(intensity)))
            return_type = 0
            channel = int(ring)

            points.append(
                (
                    float(x),
                    float(y),
                    float(z),
                    intensity_u8,
                    return_type,
                    channel,
                )
            )

        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name="intensity", offset=12, datatype=PointField.UINT8, count=1),
            PointField(name="return_type", offset=13, datatype=PointField.UINT8, count=1),
            PointField(name="channel", offset=14, datatype=PointField.UINT16, count=1),
        ]

        out = pc2.create_cloud(msg.header, fields, points)
        out.height = 1
        out.width = len(points)
        out.row_step = out.point_step * out.width
        out.is_dense = True 
        self.pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = VelodyneToAutoware()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
